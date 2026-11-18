"""Constraint-based multi-day attraction planner for MapOut."""

import math

from src.route_matrix import get_route_matrix

MAX_CSP_CANDIDATES = 20
MAX_SEARCH_NODES = 15000
REGIONAL_DISTANCE_THRESHOLD_KM = 5.0
REGIONAL_DRIVING_TRANSFER_MINUTES = 60.0
EPSILON = 1e-7


def generate_csp_itinerary(
    attractions, destination, interests, budget, days, minutes_per_day,
    transport_mode="walking", max_transfer_minutes=None,
):
    if days <= 0 or minutes_per_day <= 0 or not math.isfinite(float(budget)) or budget < 0:
        raise ValueError("Invalid trip preferences")
    if transport_mode not in ("walking", "driving"):
        raise ValueError("Invalid transportation mode")
    if max_transfer_minutes is None:
        max_transfer_minutes = 25 if transport_mode == "walking" else 20
    if not math.isfinite(float(max_transfer_minutes)) or max_transfer_minutes <= 0:
        raise ValueError("Invalid maximum transfer time")

    selected_interests = {str(x).strip().lower() for x in interests if str(x).strip()}
    if not selected_interests:
        raise ValueError("At least one interest is required")

    suitable = []
    for attraction in attractions:
        if str(attraction.get("city", "")).strip().lower() != destination.strip().lower():
            continue
        categories = attraction.get("categories", [])
        if isinstance(categories, str):
            categories = categories.split("|")
        matches = {str(x).strip().lower() for x in categories if str(x).strip()} & selected_interests
        if not matches:
            continue
        raw_price = attraction.get("estimated_cost_eur")
        price_unknown = raw_price is None or str(raw_price).strip() == ""
        try:
            cost = 0.0 if price_unknown else float(raw_price)
            duration = int(attraction["visit_duration_min"])
            lat = float(attraction["latitude"])
            lon = float(attraction["longitude"])
        except (ValueError, TypeError, KeyError):
            continue
        if not (math.isfinite(cost) and math.isfinite(lat) and math.isfinite(lon)):
            continue
        if cost < 0 or cost > budget or duration <= 0 or duration > minutes_per_day:
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        item = attraction.copy()
        item.update(_known_cost=cost, _price_unknown=price_unknown,
                    _duration=duration, _latitude=lat, _longitude=lon,
                    _interest_matches=len(matches))
        suitable.append(item)

    matching_count = len(suitable)

    def priority(item):
        return (-item["_interest_matches"], item["_duration"],
                item["_price_unknown"], item["_known_cost"],
                str(item.get("name", "")).lower())

    if len(suitable) > MAX_CSP_CANDIDATES:
        buckets = {}
        for item in suitable:
            region = str(item.get("region", "")).strip().lower() or "__unknown_region__"
            buckets.setdefault(region, []).append(item)
        for bucket in buckets.values():
            bucket.sort(key=priority)
        regions = sorted(buckets, key=lambda region: priority(buckets[region][0]))
        selected = []
        while len(selected) < MAX_CSP_CANDIDATES:
            added = False
            for region in regions:
                if buckets[region]:
                    selected.append(buckets[region].pop(0))
                    added = True
                    if len(selected) == MAX_CSP_CANDIDATES:
                        break
            if not added:
                break
        suitable = selected
    suitable.sort(key=priority)
    n = len(suitable)

    def empty_day():
        return {"attractions": [], "cost": 0.0, "known_cost": 0.0,
                "unknown_price_count": 0, "visit_minutes": 0,
                "travel_minutes": 0.0, "minutes": 0.0,
                "distance_km": 0.0, "regional_transfer_count": 0}

    if n == 0:
        return {
            "days": [empty_day() for _ in range(days)], "transport_mode": transport_mode,
            "total_cost": 0.0, "total_known_cost": 0.0, "unknown_price_count": 0,
            "cost_is_complete": True, "total_attractions": 0,
            "total_visit_minutes": 0, "total_travel_minutes": 0.0,
            "total_distance_km": 0.0, "total_matching_attractions": matching_count,
            "csp_candidates_considered": 0,
            "candidate_limit_applied": matching_count > MAX_CSP_CANDIDATES,
            "search_limit_reached": False, "search_nodes_explored": 0,
            "local_search_improvements": 0,
            "regional_transfer_minutes": (REGIONAL_DRIVING_TRANSFER_MINUTES
                                          if transport_mode == "driving" else max_transfer_minutes),
        }

    matrix = get_route_matrix(suitable, transport_mode)
    durations = matrix["durations"]
    distances = matrix["distances"]
    visit = [item["_duration"] for item in suitable]
    prices = [item["_known_cost"] for item in suitable]
    interest = [item["_interest_matches"] for item in suitable]

    # Compute each directed transfer once. None means unavailable or too long.
    legs = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                legs[i][j] = (0.0, 0.0, 0)
                continue
            try:
                time = float(durations[i][j])
                distance = float(distances[i][j])
            except (ValueError, TypeError, IndexError, KeyError):
                continue
            if not (math.isfinite(time) and math.isfinite(distance)) or time < 0 or distance < 0:
                continue
            regional = False
            if transport_mode == "driving":
                a, b = suitable[i], suitable[j]
                lat1, lat2 = math.radians(a["_latitude"]), math.radians(b["_latitude"])
                dlat = lat2 - lat1
                dlon = math.radians(b["_longitude"] - a["_longitude"])
                hav = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2)
                       * math.sin(dlon / 2) ** 2)
                straight = 12742.0 * math.asin(math.sqrt(min(1.0, max(0.0, hav))))
                regional = straight >= REGIONAL_DISTANCE_THRESHOLD_KM
            limit = (max(float(max_transfer_minutes), REGIONAL_DRIVING_TRANSFER_MINUTES)
                     if regional else float(max_transfer_minutes))
            if time <= limit + EPSILON:
                legs[i][j] = (time, distance, int(regional))

    # A day state contains an ordered route and unrounded aggregate metrics.
    def make_state(route=(), visiting=0, traveling=0.0, distance=0.0, regional=0):
        return (tuple(route), visiting, traveling, distance, regional)

    def insertions(state, candidate):
        route, visiting, traveling, distance, regional = state
        new_visiting = visiting + visit[candidate]
        if new_visiting > minutes_per_day:
            return []
        results = []
        for position in range(len(route) + 1):
            prev = route[position - 1] if position else None
            nxt = route[position] if position < len(route) else None
            old = legs[prev][nxt] if prev is not None and nxt is not None else (0.0, 0.0, 0)
            before = legs[prev][candidate] if prev is not None else (0.0, 0.0, 0)
            after = legs[candidate][nxt] if nxt is not None else (0.0, 0.0, 0)
            if old is None or before is None or after is None:
                continue
            new_travel = traveling + before[0] + after[0] - old[0]
            if new_visiting + new_travel > minutes_per_day + EPSILON:
                continue
            new_distance = distance + before[1] + after[1] - old[1]
            new_regional = regional + before[2] + after[2] - old[2]
            new_route = route[:position] + (candidate,) + route[position:]
            results.append(make_state(new_route, new_visiting, new_travel,
                                      new_distance, new_regional))
        results.sort(key=lambda s: (s[2] - traveling, s[2], s[1] + s[2], s[0]))
        return results

    initial = tuple(make_state() for _ in range(days))

    def score(states, count, interest_sum, visit_sum, cost):
        # Lexicographic objective: maximize coverage and relevance first,
        # then sightseeing, then minimize travel and distance, then balance days.
        loads = [s[1] + s[2] for s in states]
        imbalance = max(loads) - min(loads) if loads else 0.0
        return (-count, -interest_sum, -visit_sum,
                round(sum(s[2] for s in states), 7),
                round(sum(s[3] for s in states), 7),
                round(imbalance, 7),
                -sum(bool(s[0]) for s in states), round(cost, 7))

    best_states = initial
    best_score = score(initial, 0, 0, 0, 0.0)
    best_count = 0
    nodes = 0
    limit_reached = False

    # Greedy incumbent: quickly establish a useful lower bound on the number
    # of attractions, including when backtracking later hits its node limit.
    greedy_states = list(initial)
    greedy_cost = 0.0
    greedy_count = 0
    greedy_interest = 0
    greedy_visits = 0
    for i in range(n):
        if greedy_cost + prices[i] > budget + EPSILON:
            continue
        options = []
        for d in range(days):
            if not greedy_states[d][0] and any(not greedy_states[k][0] for k in range(d)):
                continue
            for candidate_state in insertions(greedy_states[d], i):
                options.append((candidate_state[2] - greedy_states[d][2],
                                candidate_state[1] + candidate_state[2], d,
                                candidate_state))
        if options:
            _, _, day_idx, chosen = min(options, key=lambda x: (x[0], x[1], x[2]))
            greedy_states[day_idx] = chosen
            greedy_cost += prices[i]
            greedy_count += 1
            greedy_interest += interest[i]
            greedy_visits += visit[i]
    greedy_states = tuple(greedy_states)
    greedy_score = score(greedy_states, greedy_count, greedy_interest, greedy_visits, greedy_cost)
    if greedy_score < best_score:
        best_states, best_score, best_count = greedy_states, greedy_score, greedy_count

    # Upper bounds on the number of remaining attractions that can fit in
    # the remaining *total* free sightseeing time (ignoring travel).
    remaining_min_durations = [None] * (n + 1)
    for i in range(n + 1):
        remaining_min_durations[i] = sorted(visit[i:])

    # Equivalent day permutations are normalized, preventing repeated searches.
    # States with the same routes and next candidate have the same future;
    # the accumulated cost is determined by the selected attraction set.
    seen = set()

    def backtrack(index, states, count, interest_sum, visit_sum, cost):
        nonlocal nodes, limit_reached, best_states, best_score, best_count
        if nodes >= MAX_SEARCH_NODES:
            limit_reached = True
            return
        nodes += 1

        current_score = score(states, count, interest_sum, visit_sum, cost)
        if current_score < best_score:
            best_states, best_score, best_count = states, current_score, count

        if index == n:
            return

        # Admissible cardinality bound: no completion can exceed this many
        # attractions, even if all remaining travel times were zero.
        free_time = days * minutes_per_day - sum(s[1] + s[2] for s in states)
        possible = 0
        time_used = 0
        for duration in remaining_min_durations[index]:
            if time_used + duration > free_time + EPSILON:
                break
            time_used += duration
            possible += 1
        if count + possible < best_count:
            return

        # If the maximum attainable count ties the incumbent, an optimistic
        # interest upper bound can still prove the branch cannot win.
        if count + possible == best_count:
            needed = best_count - count
            optimistic_interest = interest_sum + sum(sorted(interest[index:], reverse=True)[:needed])
            if optimistic_interest < -best_score[1]:
                return

        # Day labels are interchangeable because every day has the same
        # duration limit. Normalize routes only for memoization; preserve the
        # original ordering for output and insertion choices.
        signature = (index, tuple(sorted(s[0] for s in states)))
        if signature in seen:
            return
        seen.add(signature)

        if cost + prices[index] <= budget + EPSILON:
            # Prefer filling a day with compatible nearby stops. This finds
            # high-quality routes early, helping pruning under the node cap.
            branches = []
            empty_tried = False
            for d, state in enumerate(states):
                if not state[0]:
                    if empty_tried:
                        continue
                    empty_tried = True
                for new_state in insertions(state, index):
                    branches.append((new_state[2] - state[2],
                                     new_state[1] + new_state[2], d, new_state))
            branches.sort(key=lambda x: (x[0], x[1], x[2]))
            for _, _, d, new_state in branches:
                next_states = list(states)
                next_states[d] = new_state
                backtrack(index + 1, tuple(next_states), count + 1,
                          interest_sum + interest[index], visit_sum + visit[index],
                          cost + prices[index])
                if limit_reached:
                    return

        backtrack(index + 1, states, count, interest_sum, visit_sum, cost)

    backtrack(0, initial, 0, 0, 0, 0.0)

    # Local improvement phase. CSP establishes feasibility; this bounded
    # hill-climber improves its incumbent without spending more CSP nodes.
    # Moves include relocating a stop, swapping stops between days, and
    # inserting an unselected stop. Every route is revalidated from the matrix.
    def rebuild(route_indices):
        visiting = sum(visit[i] for i in route_indices)
        if visiting > minutes_per_day:
            return None
        traveling = distance = 0.0
        regional = 0
        for a, b in zip(route_indices, route_indices[1:]):
            leg = legs[a][b]
            if leg is None:
                return None
            traveling += leg[0]
            distance += leg[1]
            regional += leg[2]
        if visiting + traveling > minutes_per_day + EPSILON:
            return None
        return make_state(route_indices, visiting, traveling, distance, regional)

    def candidate_score(states):
        chosen = [i for state in states for i in state[0]]
        return score(states, len(chosen), sum(interest[i] for i in chosen),
                     sum(visit[i] for i in chosen), sum(prices[i] for i in chosen))

    # A strict improvement is accepted each iteration, preventing cycles.
    # Cap the number of iterations to keep the interactive CLI responsive.
    local_improvements = 0
    for _ in range(30):
        current = best_states
        current_score = candidate_score(current)
        next_states = current
        next_score = current_score
        chosen = {i for state in current for i in state[0]}
        available = [i for i in range(n) if i not in chosen]
        current_cost = sum(prices[i] for i in chosen)

        def consider(routes):
            nonlocal next_states, next_score
            states = []
            for route_indices in routes:
                state = rebuild(route_indices)
                if state is None:
                    return
                states.append(state)
            states = tuple(states)
            candidate = candidate_score(states)
            if candidate < next_score:
                next_score = candidate
                next_states = states

        base = [state[0] for state in current]
        # Add previously skipped attractions, including ones excluded by
        # early search-limit termination.
        for i in available:
            if current_cost + prices[i] > budget + EPSILON:
                continue
            for d in range(days):
                for pos in range(len(base[d]) + 1):
                    routes = list(base)
                    routes[d] = base[d][:pos] + (i,) + base[d][pos:]
                    consider(routes)

        # Relocate any selected attraction, including within its own day.
        for source_day in range(days):
            for source_pos, item in enumerate(base[source_day]):
                removed = base[source_day][:source_pos] + base[source_day][source_pos + 1:]
                for target_day in range(days):
                    target = removed if target_day == source_day else base[target_day]
                    for pos in range(len(target) + 1):
                        routes = list(base)
                        routes[source_day] = removed
                        routes[target_day] = target[:pos] + (item,) + target[pos:]
                        consider(routes)

        # Swap selected stops between days. Cost and attraction count stay
        # unchanged, but route feasibility and time limits are rechecked.
        for a in range(days):
            for b in range(a + 1, days):
                for pa, ia in enumerate(base[a]):
                    for pb, ib in enumerate(base[b]):
                        routes = list(base)
                        ra, rb = list(base[a]), list(base[b])
                        ra[pa], rb[pb] = ib, ia
                        routes[a], routes[b] = tuple(ra), tuple(rb)
                        consider(routes)

        if next_score >= current_score:
            break
        best_states, best_score = next_states, next_score
        best_count = sum(len(state[0]) for state in best_states)
        local_improvements += 1

    def format_day(state):
        route, visiting, traveling, distance, regional = state
        known_cost = sum(prices[i] for i in route)
        unknown = sum(suitable[i]["_price_unknown"] for i in route)
        return {
            "attractions": [suitable[i] for i in route],
            "cost": round(known_cost, 2),
            "known_cost": round(known_cost, 2),
            "unknown_price_count": unknown,
            "visit_minutes": visiting,
            "travel_minutes": round(traveling, 1),
            "minutes": round(visiting + traveling, 1),
            "distance_km": round(distance, 2),
            "regional_transfer_count": regional,
        }

    daily = [format_day(state) for state in best_states]
    known_total = round(sum(d["known_cost"] for d in daily), 2)
    unknown_total = sum(d["unknown_price_count"] for d in daily)
    return {
        "days": daily,
        "transport_mode": transport_mode,
        "total_cost": known_total,
        "total_known_cost": known_total,
        "unknown_price_count": unknown_total,
        "cost_is_complete": unknown_total == 0,
        "total_attractions": sum(len(d["attractions"]) for d in daily),
        "total_visit_minutes": sum(d["visit_minutes"] for d in daily),
        "total_travel_minutes": round(sum(s[2] for s in best_states), 1),
        "total_distance_km": round(sum(s[3] for s in best_states), 2),
        "total_matching_attractions": matching_count,
        "csp_candidates_considered": n,
        "candidate_limit_applied": matching_count > MAX_CSP_CANDIDATES,
        "search_limit_reached": limit_reached,
        "search_nodes_explored": nodes,
        "local_search_improvements": local_improvements,
        "regional_transfer_minutes": (REGIONAL_DRIVING_TRANSFER_MINUTES
                                      if transport_mode == "driving" else max_transfer_minutes),
    }
