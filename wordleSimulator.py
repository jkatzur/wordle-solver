# Simulation
# * Update simulator to have flat curve (any random 0 to 10k or weighted guessing by frequency)
# * Wrap simulator so I can simulate 10,000 games with any ranking approach (and number of letters)
# * Create data structure of per-game info on number of guesses to correct to compare
# * Further wrap simulator in for loop with various params for each of the above, like a matrix of outcomes


class wordleSimulator:
    def __init__(self, n_letters = 5, sims = 1000, log_to = 'simulation_log.csv'):
        self.n_letters = n_letters
        self.sims = sims
        self.log_to = log_to
        
    # Run the simulation
    def run_simulations(self):
        game = 0
        while game < self.sims:
            # Setup game
            wordleGame = wordleGame(self.n_letters)
            wordleSolver = wordleSolver(self.n_letters)
            # Setup loop for gameplay
