# Science Simulation Lab Agent

An offline, interactive science simulation lab for high school students that converts textual exercises into dynamic, interactive simulations.

## Features

- Text-to-simulation conversion for science exercises
- Interactive 2D motion graphics
- Real-time parameter adjustment
- Offline operation
- Educational feedback and guidance

## Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/science-simulation-lab-agent.git
cd science-simulation-lab-agent

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m science_simulator
```

## Project Structure

```
science-simulation-lab-agent/
├── science_simulator/     # Main package
│   ├── core/              # Core simulation logic
│   ├── ui/                # User interface components
│   ├── models/            # Data models
│   ├── parsers/           # Text parsing and conversion
│   └── utils/             # Utility functions
├── tests/                 # Unit and integration tests
├── data/                  # Simulation data and assets
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## License

MIT License
