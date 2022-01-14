from typing import List
import random
from wordfreq import get_frequency_dict
import pandas

# Implements wordle solver for wordle puzzle of n_letters
# This first solver just ranks words by their wordfreq
class wordleSolver:
    def __init__(self, n_letters: int):
        self.n_letters = n_letters
        self.letters_in = set()
        self.letters_out = set()
        self.pos_yes = [set() for _ in range(n_letters)]
        self.pos_no = [set() for _ in range(n_letters)]
        self.guesses = []
        self.possible_words = self.load_start_words()
        self.letter_scores_by_word = {}
        self.letter_scores_by_freq = {}

        self.update_state()        
        
    def load_start_words(self):
        try:
            return pandas.read_pickle(f"./start_words/start_words_{self.n_letters}_letters.pkl")
        except:
            pos_words = self.possible_words()
            pos_words.to_pickle(f"./start_words/start_words_{self.n_letters}_letters.pkl")
            return pos_words

    # Return list of all possible words of n_letter length as a dict with wordfreq
    def possible_words(self) -> List[int]:
        freq_dict = get_frequency_dict('en', wordlist='best')
        n_letter_words = []
        for w in freq_dict.items():
            if len(w[0]) == self.n_letters and w[0].isalpha(): #removes non-alpha words like don't
                n_letter_words.append(w)
        df = pandas.DataFrame(n_letter_words)
        df.columns = ['word', 'freq']
        return df
    
    # Given a guess and a response this updates state including updating possible_words
    def process_guess(self, guess: str, response: List[int]) -> dict:
        self.guesses.append({'guess': guess, 'response': response})
        for i, r in enumerate(response):
            if r == '_':
                self.letters_out.add(guess[i])
            elif r == '-':
                self.letters_in.add(guess[i])
                self.pos_no[i].add(guess[i])
            elif r == '+':
                self.letters_in.add(guess[i])
                self.pos_yes[i].add(guess[i])

        self.possible_words = self.possible_words[self.possible_words.iloc[:,0:].apply(self.word_in, axis=1)]
        self.update_state()

    # Package the non-turn based state updates for use during init and as part of turn processing
    def update_state(self):
        self.update_letter_scores()
        # Should combine into one scan on the word col
        self.possible_words['letter_score_by_word'] = self.possible_words.apply(lambda row: self.score_word_letter_scores(row[0], False), axis = 1)
        self.possible_words['letter_score_by_freq'] = self.possible_words.apply(lambda row: self.score_word_letter_scores(row[0], True), axis = 1)
        self.possible_words['distinct_letters'] = self.possible_words.apply(lambda row: len(set(row[0])), axis = 1)
        # Normalize model input columns
        for col in ['freq', 'letter_score_by_word', 'letter_score_by_freq', 'distinct_letters']:
            self.possible_words[col] = self.possible_words[col] / self.possible_words[col].max()


    # This is the method that is overridden in more advanced solvers
    def next_guess(self, sort_on:str = 'model_rank', model_params:dict = \
                    {'freq': 1, 'letter_score_by_word': 1, 'letter_score_by_freq': 1, 'distinct_letters': 1}) -> str:
        
        self.possible_words['model_rank'] = sum(model_params[weight] * self.possible_words[weight] for weight in model_params.keys())
        return self.possible_words.sort_values(sort_on, ascending=False).iloc[0]['word']

    # Return top n rows by some method/params. Use same params as guess to evaluate consistently!
    def top_n_by(self, n:int = 20, sort_on:str = 'model_rank', model_params:dict = \
                    {'freq': 1, 'letter_score_by_word': 1, 'letter_score_by_freq': 1, 'distinct_letters': 1}):
        
        self.possible_words['model_rank'] = sum(model_params[weight] * self.possible_words[weight] for weight in model_params.keys())
        return self.possible_words.sort_values(sort_on, ascending=False).head(n)

    
    # Calculates the per-letter likelihood of each letter in the remaining possible words
    def update_letter_scores(self) -> float:
        words_by_letter = {}
        words_by_letter_weighted = {}
        perc_by_letter = {}

        for index, row in self.possible_words.iterrows():
            for l in set(row[0]):
                if l in words_by_letter:
                    if l not in self.letters_in:
                        words_by_letter[l] += 1
                        words_by_letter_weighted[l] += row[1]
                else:
                    words_by_letter[l] = 1
                    words_by_letter_weighted[l] = row[1]
        for key in words_by_letter.keys():
            perc_by_letter[key] = 1.0 * words_by_letter[key] / sum(words_by_letter.values())

        self.letter_scores_by_freq = dict(sorted(words_by_letter_weighted.items(), key=lambda item:item[1], reverse=True))
        self.letter_scores_by_word = dict(sorted(perc_by_letter.items(), key=lambda item:item[1], reverse=True))

    # Calculates the letter scores for a specific word based on the current state of self.letter_scores or self.letter_scores_weighted
    def score_word_letter_scores(self, w, weighted=True):
        letter_val_score = 0
        # letter_val_score_weighted = 0
        for l in set(w):
            if weighted:
                letter_val_score += self.letter_scores_by_freq[l]
            else:
                letter_val_score += self.letter_scores_by_word[l]
            # letter_val_score_weighted += self.letter_scores_weighted[l]

        return letter_val_score

    # Determines if a given word matches all conditions in current state. Could improve by only evaluating new conditions
    def word_in(self, w):
        if 1 in [c in w[0] for c in self.letters_out]:
            return False
        # Check if all letters in are there
        if not sum([c in w[0] for c in self.letters_in])==len(self.letters_in):
            return False
        # Check pos_yes
        for i in range(self.n_letters):
            if self.pos_no[i] and w[0][i] in self.pos_no[i]:
                return False
            if self.pos_yes[i] and w[0][i] not in self.pos_yes[i]:
                return False
        return True



# For when you are running the solver via command line
if __name__ == '__main__':
    # Pick a length of game we're trying to solve
    while True:
        try: 
            n_letters = int(input("\nWhat length wordle game are we trying to solve? Enter a number 2 through 15.\t"))
            if 2 <= n_letters <= 15:
                break
            else:
                print("Pick a number 2 to 15")
        except ValueError:
            print("Please enter an integer from 2 to 15")

    # Setup the wordle solver
    wordleSolver = wordleSolver(n_letters = n_letters)

    game_on = True

    # Core solver loop
    print(f"\nFYI - input guesses by just the characters, e.g `query` (no backticks though, just the 5 characters)")
    print(f"Share response using `+` for correct location, `-` for incorrect, `_` for not in word, e.g `_+__-`")
    print(f"From the app, green letters are +, yellow - and gray are _")
    print(f"\n\n---- Starting wordle solver for {n_letters} letter word ----")

    turn = 1
    while game_on:
        print(f"Currently potential matched words is: {len(wordleSolver.possible_words)}")
        print(f"Top guess based on our model is: {wordleSolver.next_guess()}")

        # Would you like to see more
        while True:
            see_top = input(f"Would you like to see the top 20 possible words? Y(es) or N(o)? {'' : >3}").upper()
            if see_top == 'Y' or see_top == 'N':
                break
            else:
                print(f"Sorry, try again.")

        if see_top == 'Y':
            print(f"\nTop 20 suggested guesses are:")
            print(wordleSolver.top_n_by(20))
            print("\n")
        
        # Input guess
        while True:
            guess = input(f"Turn {turn}. Input your guess: {'' : >5}").lower()
            if guess.isalpha and len(guess) == n_letters:
                break
            else:
                print(f"Sorry, try again.")

        # Input response you got
        while True:
            raw_response = input(f"Input the response you got: {'' : >3}").lower()
            if sum([1 for l in raw_response if l in '+-_']) == n_letters:
                break
            else:
                print(f"Sorry, try again.")

        if sum([1 for r in raw_response if r == '+']) == n_letters:
            print(f"Congrats on winning in {turn} turns!")
            break

        wordleSolver.process_guess(guess=guess, response=list(raw_response))

        turn += 1