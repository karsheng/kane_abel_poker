# Kane and Abel Poker AI

## About the Project

"Kane and Abel" is a project dedicated to the development of advanced artificial intelligence solutions for poker, a complex multi-agent environment with hidden information. We present two AI entities, `Kane` and `Abel`, with distinct strategies to approach the poker challenge. Kane leans on deterministic heuristics and FSM while Abel exploits the Counterfactual Regret Minimization paradigm. Accompanying these AIs is a complementary web application tailored for players to engage in poker matches and learn from their AI opponents.

<div style="text-align:center">
    <img src="assets/poker.jpeg" alt="Kane Abel Poker" width="100%"/>
</div>

## Installation

1. First, you'll need to clone the repository:

   ```sh
   git clone https://github.com/karsheng/kane_abel_poker.git
   ```

2. Navigate to the project directory:

   ```sh
   cd kane_abel_poker
   ```

3. It's recommended to use a virtual environment. Set one up using `venv`:

   ```sh
   python3 -m venv venv
   ```

4. Activate the virtual environment:

   - On macOS and Linux:

     ```sh
     source venv/bin/activate
     ```

   - On Windows:
     ```sh
     .venvScriptsactivate
     ```

5. Install the required packages using the `requirements.txt` file:
   ```sh
   pip install -r requirements.txt
   ```

## Running the WebApp

To start the web application, navigate to the webapp directory and run the poker.py script:

```sh
python webapp/server/poker.py
```

The application should now be running on your localhost. Open a browser and navigate to the provided address, usually `http://127.0.0.1:8888/` unless specified otherwise.

Remember to deactivate the virtual environment when you're done:

```sh
deactivate
```

## Live Demo

Check out the live demo of the project [here](https://kane-abel-poker-8ed0c35431e5.herokuapp.com/).

## Acknowledgements

- Special thanks to the contributors and everyone involved in providing feedback to improve the AIs.
