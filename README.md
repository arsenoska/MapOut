# MapOut – AI-Powered Travel Planner

## Project Overview

MapOut is an AI-powered travel planning application designed to help users organize trips based on their interests, budget, and available time. The system aims to recommend suitable attractions and generate personalized travel itineraries.

The initial prototype focuses on Ohrid, North Macedonia.

## Week 4 – Data and Environment Representation

The goal of Week 4 was to prepare the initial dataset and represent the travel planning environment so it can be used by search algorithms in later weeks.

### Dataset

The dataset is stored in `attractions.csv` and contains 15 attractions in Ohrid and the surrounding area.

Each attraction includes:

- `id` – Unique attraction identifier.
- `name` – Name of the attraction.
- `category` – Type of activity (History, Adventure, Relaxation, Food, or Entertainment).
- `latitude` – Geographic latitude.
- `longitude` – Geographic longitude.
- `estimated_cost_eur` – Estimated cost in euros; empty if unknown.
- `visit_duration_min` – Estimated visit duration in minutes.
- `availability` – Visiting conditions or opening information.
- `source` – Website used as a reference for the attraction.

Visit durations are planning estimates. Some admission prices, opening hours, and coordinates require further verification.

### Environment Representation

The environment consists of attractions that can be selected when planning a trip.

- **State:** The attractions already selected, remaining budget, remaining available time, and current location.
- **Actions:** Select an attraction or move to another attraction.
- **Transition:** Update the itinerary, remaining budget, remaining time, and current location after an action.
- **Goal:** Generate an itinerary that fits the user's interests, budget, and available time.

This is the planned search representation. The Week 4 implementation prepares the attraction data; it does not yet implement the full state-transition model.

### Data Loading and Validation

The program uses Python's built-in `csv` module to read `attractions.csv`.

It checks for:

- Missing attraction names.
- Invalid categories.
- Missing or invalid geographic coordinates.
- Coordinates outside valid latitude and longitude ranges.
- Missing, invalid, or negative costs.
- Invalid or non-positive visit durations.

Missing costs are represented as unknown rather than automatically treated as free.

### Data Sources and Limitations

Attraction information was collected from museum websites, tourism websites, and travel guides. Each attraction has a source reference in the CSV, except where verification is still pending.

Some links provide general information about an attraction but do not independently verify every field. Opening hours and admission prices may change, so unknown values are kept explicitly rather than guessed.

### How to Run

Requirements: Python 3.

Place `main.py` and `attractions.csv` in the same folder, then run:

```bash
python main.py
```

The program reads the dataset, validates attraction information, and displays the results in the terminal.

### Testing

The dataset was tested with 15 attractions. Validation was also tested using an intentionally invalid latitude value to check that the program identifies coordinates outside the allowed range.

### Next Steps

In Week 5, the project will use the prepared dataset to implement and test a baseline search approach for generating travel itineraries.