# Refrigeration Calculator

The program aims to simulate a theoretical refrigeration cycle -- given inputs such as temperature, pressure, superheat / subcooling, and compressor efficiency. There are several refrigerants
the user can choose from. The properties were determined using the CoolProp library and results were verified against the IRC Fluid calculator online and Cengel's Engineering Thermodynamics.
The simple version evaluates the performance of a refrigeration cycle by prompting the user in the terminal. The GUI version allows for interaction with dropdown menus and an output table. The Streamlit
version (courtesy of Lasse Thomsen) allowed me to host the program as a web-based app.

I included a PDF of an example refrigeration cycle problem from the ASHRAE fundamentals book... as verification for potential users :)

Link to a web based version of the program: https://numerous.com/app/share/2cb12d02-49ef-4dc5-b0a0-efc9585a6554

## Setup

- Create virtualenv with `python3 -m venv venv`
- `source venv/bin/activate`
- install off requirements with `pip install -r requirements.txt`
  - to update requirements use `pip freeze > requirements.txt`

## Building an executable

Build the program to `dist/` using `pyinstaller -F filename.py`

### To deploy the app on Numerous

- Install the dev requirements with `pip install -r requirements-dev.txt`
- Run `numerous deploy -o your-org-slug`. You can find your org slug by running `numerous orgarnization list` after you have signed up for free on numerous.com.
 can find your org slug by running `numerous orgarnization list` after you have signed up for free on numerous.com.
