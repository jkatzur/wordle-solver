import csv
import datetime
from logging import log
import pandas
from wordleGame import wordleGame
from wordleSolver import wordleSolver
from os.path import exists

# Simulation
# * Update simulator to have flat curve (any random 0 to 10k or weighted guessing by frequency)
# * Wrap simulator so I can simulate 10,000 games with any ranking approach (and number of letters)
# * Create data structure of per-game info on number of guesses to correct to compare
# * Further wrap simulator in for loop with various params for each of the above, like a matrix of outcomes

def run_simulation(n_letters:int = 5, sims:int = 1000, log_to:str = './simulations/test.csv', log_output:bool = True,
            cl_output:bool = False, start_word:str = None):
    
    game_num = 0
    if log_output:
        if not exists(log_to):
            log_file = csv.writer(open(log_to, 'w'))
            log_file.writerow(['game_num', 'completed_at', 'first_guess', 'word', 'turns'])
        else:
            log_file = csv.writer(open(log_to, 'a'))

    while game_num < sims:
        # Setup game
        wordle_game = wordleGame(n_letters)
        wordle_solver = wordleSolver(n_letters)
        
        game_on = True
        turn = 1

        attributes = {"game_num": game_num}
        
        while game_on:
            guess = wordle_solver.next_guess()

            if turn == 1 and start_word:
                guess = start_word
            
            response = wordle_game.respond_guess(guess)
            
            if turn == 1:
                attributes['first_guess'] = guess
            if cl_output:
                print(f"Turn: {turn}. Guess: {guess}, Response: {response['response']}")
            if response['win']:
                attributes['word'] = guess
                attributes['completed_at'] = datetime.datetime.now()
                if log_output:
                    log_file.writerow([attributes['game_num'], attributes['completed_at'], attributes['first_guess'], attributes['word'], turn])
                if cl_output:
                    print(f"Won in {turn} turns")
                game_on = False
            
            wordle_solver.process_guess(guess, response["response"])
            turn += 1

        game_num += 1
            

    # For when you are running a game via the command line
if __name__ == '__main__':
    
    first_words_to_test = ['about', 'their', 'there', 'which', 'would', 'other', 'after', 'first', 'think', 'could',
    'these', 'where', 'right', 'years', 'being', 'going', 'still', 'never', 'those', 'world']

    for w in first_words_to_test:
        print(f"Working on: {w}...")
        run_simulation(n_letters=5, sims=100, log_to='./simulations/freq_only.csv', log_output=True, cl_output=False, start_word=w)