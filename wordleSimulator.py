import csv
import datetime
from logging import log
import pandas
from wordleGame import wordleGame
from wordleSolver import wordleSolver
from os.path import exists
import hashlib
import time

# Simulation
# * Update simulator to have flat curve (any random 0 to 10k or weighted guessing by frequency)
# * Wrap simulator so I can simulate 10,000 games with any ranking approach (and number of letters)
# * Create data structure of per-game info on number of guesses to correct to compare
# * Further wrap simulator in for loop with various params for each of the above, like a matrix of outcomes

def run_simulation(n_letters:int = 5, sims:int = 1000, game_log:str = None, turn_log:str = None,
        start_word:str = None, sort_on:str = 'model_rank', model_params:dict = \
                    {'freq': 1, 'letter_score_by_word': 1, 'letter_score_by_freq': 1, 'distinct_letters': 1}):
    
    game_num = 0
    if game_log:
        if not exists(game_log):
            game_log_file = csv.writer(open(game_log, 'w'))
            game_log_file.writerow(['game_id', 'start_at', 'completed_at', 'n_letters', 'first_guess', 'sort_on', 'model_params', 'word', 'turns'])
        else:
            game_log_file = csv.writer(open(game_log, 'a'))

    if turn_log:
        if not exists(turn_log):
            turn_log_file = csv.writer(open(turn_log, 'w'))
            turn_log_file.writerow(['game_id', 'turn_number', 'guess', \
                'words_possible', 'letters_in', 'letters_out', 'pos_yes', 'pos_no', \
                'freq', 'letter_score_by_word', 'letter_score_by_freq', 'distinct_letters', \
                'model_params', 'model_rank', 'response'])
        else:
            turn_log_file = csv.writer(open(turn_log, 'a'))

    while game_num < sims:
        # Create new game and solver
        wordle_game = wordleGame(n_letters)
        wordle_solver = wordleSolver(n_letters)

        # Setup logging for game
        game_attributes = {'start_at': datetime.datetime.now(), 'sort_on': sort_on, 'model_params': model_params, 'n_letters': n_letters}
        
        # Create game_id from hash of current_time. Will use this to join game and turnid later
        hash = hashlib.sha1()
        hash.update(str(time.time()).encode('utf-8'))
        game_id = str(game_num) + str(hash.hexdigest()[:12])
        game_attributes['game_id'] = game_id

        turn = 1
        game_on = True
        while game_on:
                
            if turn == 1 and start_word:
                guess = start_word
            else:
                guess = wordle_solver.next_guess()
            
            if turn == 1:
                game_attributes['first_guess'] = guess

            response = wordle_game.respond_guess(guess)

            if turn_log:
                word_info = wordle_solver.top_n_by(1).iloc[0]
                turn_attributes = {'game_id': game_id,
                    'turn_number': turn,
                    'guess': guess,
                    'words_possible': len(wordle_solver.possible_words),
                    'letters_in': list(wordle_solver.letters_in),
                    'letters_out': list(wordle_solver.letters_out),
                    'pos_yes': [list(pos_yes) for pos_yes in wordle_solver.pos_yes],
                    'pos_no': [list(pos_no) for pos_no in wordle_solver.pos_no]}
                for c in ['freq', 'letter_score_by_word', 'letter_score_by_freq', 'distinct_letters','model_rank']:
                    turn_attributes[c] = word_info[c]
                turn_attributes['model_params'] = model_params
                turn_attributes['response'] = response['response']
                turn_log_file.writerow([turn_attributes[key] for key in ['game_id', 'turn_number', 'guess', \
                    'words_possible', 'letters_in', 'letters_out', 'pos_yes', 'pos_no', \
                    'freq', 'letter_score_by_word', 'letter_score_by_freq', 'distinct_letters', \
                    'model_params', 'model_rank', 'response']])
            
            # print(f"Turn: {turn}. Guess: {guess}, Response: {response['response']}")
            
            if response['win']:
                game_attributes['word'] = guess
                game_attributes['completed_at'] = datetime.datetime.now()
                game_attributes['turns'] = turn
                # print(f"Won in {turn} turns")
                if game_log:
                    game_log_file.writerow([game_attributes[key] for key in ['game_id', 'start_at', 'completed_at', 'n_letters', 'first_guess', 'sort_on', 'model_params', 'word', 'turns']])
                game_on = False
            
            wordle_solver.process_guess(guess, response["response"])
            turn += 1

        game_num += 1
            

    # For when you are running a game via the command line
if __name__ == '__main__':
    
    # first_words_to_test = ['about', 'their', 'there', 'which', 'would', 'other', 'after', 'first', 'think', 'could',
    # 'these', 'where', 'right', 'years', 'being', 'going', 'still', 'never', 'those', 'world']

    # next_words_to_test = ['great','while','every','state','three','since','under','thing','house','place','again','found',
    # 'might','money','night','until','doing','group','women', 'start','times', 'today','point', 'music','power', 'water',
    # 'based','small','white','later','order','party','thank','using','black','makes','whole','maybe','story','games','least',
    # 'means','early','local','video','young','court','given','level','often','death','hours','south','known','large','wrong',
    # 'along','needs','class','close','comes','looks','cause','happy','human','woman','leave','north','watch','light','short',
    # 'taken','third','among','check','heart','asked','child','major','media']


    # Top words modeled approach
    top_model_words_to_test = ['their', 'about', 'other', 'after', 'years', 'great', 'those', 'raise', 'there', 'rates',
            'later', 'arise', 'aires', 'aries', 'arose', 'tears', 'stare', 'artie', 'irate', 'taser', 'aster', 'least',
            'first', 'oates', 'share', 'heart', 'arnie', 'reina', 'raine', 'einar', 'irena', 'earns', 'snare', 'nears',
            'arent', 'siena', 'anise', 'eason', 'earth', 'laser', 'learn', 'eatin', 'ariel', 'eaton', 'earls', 'reals', 'arles']

    for w in top_model_words_to_test:
        print(f"Working on: {w}...")
        run_simulation(n_letters=5, sims=100, game_log='./simulations/gamelog_model.csv', turn_log='./simulations/turnlog_model.csv', start_word=w)

    # run_simulation(n_letters=5, sims=100, game_log='./simulations/gamelog_model.csv', turn_log='./simulations/turnlog_model.csv', start_word=None)