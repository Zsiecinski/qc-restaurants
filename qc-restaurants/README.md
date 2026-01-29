# Quezon City Restaurants Guide

A comprehensive Flask web application showcasing the best restaurants in Quezon City. Features include filtering by cuisine, price range, and accessibility options, along with an interactive map view.

## Features

- Restaurant listings with detailed information
- Interactive filtering system
- Mobile-responsive design
- Location-based search
- Accessibility information
- Price range indicators
- Cuisine type categorization

## Tech Stack

- Python 3.x
- Flask
- Pandas
- Bootstrap
- Leaflet.js for mapping

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/qc-restaurants.git
cd qc-restaurants
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

## Deployment

The application is configured for deployment on a VPS using:
- Nginx as reverse proxy
- Gunicorn as WSGI server

Deployment instructions are available in the deployment guide.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 