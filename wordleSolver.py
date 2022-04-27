# Implements wordle solver for wordle puzzle of n_letters
# This initial solver works on 'hard mode' only (only suggests words that are still possible)
# And ranks guesses by the word frequency and likelihood of the letters + position of letters
# In the remaining possible words
# The composite rank scores the various features based on simulations I ran - check out  wordleSimulator.py

# This can be improved by (1) ranking guesses by entropy (value of guess in reducing universe of potential words)
# and (2) incorporating prior guesses/results to dynamically improve model weights
# and (3) using the actual wordle corpus of words. I found it more fun to make it more general

from typing import List
from wordfreq import get_frequency_dict
import pandas

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
        self.letter_scores_pos_perc = [dict() for _ in range(self.n_letters)]
        self.letter_scores_pos_freq = [dict() for _ in range(self.n_letters)]

        self.update_state()        
        
    # Load potential words for this length. If I've already downloaded the corpus re-use it. 
    def load_start_words(self):
        try:
            return pandas.read_pickle(f"./start_words/start_words_{self.n_letters}_letters.pkl")
        except:
            pos_words = self.possible_words()
            pos_words.to_pickle(f"./start_words/start_words_{self.n_letters}_letters.pkl")
            return pos_words

    # Return list of all possible words of n_letter length as a dict including wordfreq
    def possible_words(self) -> List[int]:
        freq_dict = get_frequency_dict('en', wordlist='best')
        n_letter_words = []
        for w in freq_dict.items():
            if len(w[0]) == self.n_letters and w[0].isalpha(): #removes non-alpha words like don't
                n_letter_words.append(w)
        df = pandas.DataFrame(n_letter_words)
        df.columns = ['word', 'freq']
        # arbitrary to take top 20000 words. I chose not to use the wordle corpus so this limits to words people know
        return df.head(20000)
    
    # Given a guess and a response update state including updating possible_words and the various scores
    def process_guess(self, guess: str, response: List[int]) -> dict:
        self.guesses.append({'guess': guess, 'response': response})
        for pos, r in enumerate(response):
            if r == '_':
                # Make sure we don't incorrectly add a letter as out if the guess has double letter (e.g 'scars')
                if guess.count(guess[pos]) > 1: # are there double letters
                    # do any responses indicate the letter is present (but not in that position)
                    if [response[i] for i, c in enumerate(guess) if c == guess[pos]].count('_') == guess.count(guess[pos]):
                        self.letters_out.add(guess[pos])    
                else:
                    self.letters_out.add(guess[pos])
            elif r == '-':
                self.letters_in.add(guess[pos])
                self.pos_no[pos].add(guess[pos])
            elif r == '+':
                self.letters_in.add(guess[pos])
                self.pos_yes[pos].add(guess[pos])

        self.possible_words = self.possible_words[self.possible_words.iloc[:,0:].apply(self.word_in, axis=1)]
        # Address case when only 1 possible word... in that case just tell them that 1 word! 
        if len(self.possible_words) != 1:
            self.update_state()


    # Package the non-turn based state updates for use during init and as part of turn processing
    def update_state(self):
        self.update_letter_scores()
        # Should combine into one scan on the word col
        self.possible_words['letter_score_by_word'] = self.possible_words.apply(lambda row: self.score_word_letter_scores(row[0], False), axis = 1)
        self.possible_words['letter_score_by_freq'] = self.possible_words.apply(lambda row: self.score_word_letter_scores(row[0], True), axis = 1)
        self.possible_words['letter_score_pos_perc'] = self.possible_words.apply(lambda row: self.score_word_pos_scores(row[0], False), axis = 1)
        self.possible_words['letter_score_pos_freq'] = self.possible_words.apply(lambda row: self.score_word_pos_scores(row[0], True), axis = 1)
        self.possible_words['distinct_letters'] = self.possible_words.apply(lambda row: len(set(row[0])), axis = 1)
        # Normalize model input columns
        for col in ['freq', 'letter_score_by_word', 'letter_score_by_freq', 'letter_score_pos_perc', 'letter_score_pos_freq']:
            self.possible_words[col] = self.possible_words[col] / self.possible_words[col].max()
        
        # Normalize distinct letters by punishing non-max more
        self.possible_words['distinct_letters'] = 1 - (2.0 * (self.possible_words['distinct_letters'].max() - self.possible_words['distinct_letters']) / self.n_letters)
        self.possible_words['distinct_letters'].clip(0, 1)


    # This uses the remaining words and features to propose a single guess
    # Arguments are weights to various features. Should be overridden as we learn moer
    def next_guess(self, sort_on:str = 'model_rank', model_params:dict = \
                    {'freq': 1, 'letter_score_by_word': 1, 'letter_score_by_freq': 1,
                    'letter_score_pos_perc': 1, 'letter_score_pos_freq': 1, 'distinct_letters': 1}) -> str:
        
        self.possible_words['model_rank'] = sum(model_params[weight] * self.possible_words[weight] for weight in model_params.keys())
        return self.possible_words.sort_values(sort_on, ascending=False).iloc[0]['word']

    # Return top n rows ranked by the feature weights
    # Useful to expose to people who want to pick their guess word
    def top_n_by(self, n:int = 20, sort_on:str = 'model_rank', model_params:dict = \
                    {'freq': 1, 'letter_score_by_word': 1, 'letter_score_by_freq': 1,
                    'letter_score_pos_perc': 1, 'letter_score_pos_freq': 1, 'distinct_letters': 1}):
        
        self.possible_words['model_rank'] = sum(model_params[feature] * self.possible_words[feature] for feature in model_params.keys())
        return self.possible_words.sort_values(sort_on, ascending=False).head(n)

    
    # Calculates the per-letter likelihood of each letter in the remaining possible words
    # This can be thought of as what percent of remaining words contain each letter
    def update_letter_scores(self) -> float:
        words_by_letter = {}
        words_by_letter_weighted = {}
        perc_by_letter = {}

        words_by_letter_pos_count = [dict() for _ in range(self.n_letters)]
        words_by_letter_pos_perc = [dict() for _ in range(self.n_letters)]
        words_by_letter_pos_weighted = [dict() for _ in range(self.n_letters)]

        # TODO: combine this into fewer loops
        for index, row in self.possible_words.iterrows():
            # Any position counter
            for l in set(row[0]):
                if l in words_by_letter:
                    if l not in self.letters_in:
                        words_by_letter[l] += 1
                        words_by_letter_weighted[l] += row[1]
                else:
                    words_by_letter[l] = 1
                    words_by_letter_weighted[l] = row[1]

            # Specific position. This asks the question what percent of remaining possible words
            # have this letter in a specific position (e.g 'a' in the second position)
            for l in range(self.n_letters):
                if row[0][l] in words_by_letter_pos_count[l]:
                    words_by_letter_pos_count[l][row[0][l]] += 1
                    words_by_letter_pos_weighted[l][row[0][l]] += row[1]
                else:
                    if (row[0][l] not in self.letters_in and row[0][l] not in self.letters_out):
                        words_by_letter_pos_count[l][row[0][l]] = 1
                        words_by_letter_pos_weighted[l][row[0][l]] = row[1]

        for key in words_by_letter.keys():
            perc_by_letter[key] = 1.0 * words_by_letter[key] / sum(words_by_letter.values())

        for index in range(len(words_by_letter_pos_count)):
            s = sum(words_by_letter_pos_count[index].values())
            for k, v in words_by_letter_pos_count[index].items():
                words_by_letter_pos_perc[index][k] = v / s

        # TODO check if I still use the sorting here. I don't think so
        self.letter_scores_by_freq = dict(sorted(words_by_letter_weighted.items(), key=lambda item:item[1], reverse=True))
        self.letter_scores_by_word = dict(sorted(perc_by_letter.items(), key=lambda item:item[1], reverse=True))
        self.letter_scores_pos_perc = words_by_letter_pos_perc
        self.letter_scores_pos_freq = words_by_letter_pos_weighted

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

    # Calculates by position
    def score_word_pos_scores(self, w, weighted=True):
        letter_pos_score = 0
        # letter_val_score_weighted = 0
        for i, l in enumerate(w):
            if l in self.letter_scores_pos_perc[i]:
                if weighted:
                    letter_pos_score += self.letter_scores_pos_freq[i][l]
                else:
                    letter_pos_score += self.letter_scores_pos_perc[i][l]

        return letter_pos_score

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



# This main runs the solver via command line
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
    wordle_solver = wordleSolver(n_letters = n_letters)

    game_on = True

    # Core solver loop
    print(f"\nFYI - input guesses by just the characters, e.g `query` (no backticks though, just the 5 characters)")
    print(f"Share response using `+` for correct location, `-` for incorrect, `_` for not in word, e.g `_+__-`")
    print(f"From the app, green letters are +, yellow - and gray are _")
    print(f"\n\n---- Starting wordle solver for {n_letters} letter word ----")

    turn = 1
    # Note, I picked specific weights for each feature here, which change over time depending on which turn
    # These can be improved by more careful analysis and making a real learning system
    # Also should package the structure for .next_guess and .top_n_by so they use the same weights without copy pasta
    while game_on:
        print(f"Currently potential matched words is: {len(wordle_solver.possible_words)}")
        print(f"Top guess based on our model is: {wordle_solver.next_guess(sort_on='model_rank', model_params={'freq':0.2 * turn, 'letter_score_by_word': 0.3/turn, 'letter_score_by_freq': .3/turn, 'letter_score_pos_perc': 1.5/turn, 'letter_score_pos_freq': 1.5/turn, 'distinct_letters': 1.2})}")

        # Would you like to see more possible words?
        while True:
            see_top = input(f"Would you like to see the top 20 possible words? Y(es) or N(o)? {'' : >3}").upper()
            if see_top == 'Y' or see_top == 'N':
                break
            else:
                print(f"Sorry, try again.")

        if see_top == 'Y':
            print(f"\nTop 20 suggested guesses are:")
            print(wordle_solver.top_n_by(n=20, sort_on='model_rank', model_params={'freq':0.2 * turn, 'letter_score_by_word': 0.3/turn, 'letter_score_by_freq': 0.3/turn, 'letter_score_pos_perc': 1.5/turn, 'letter_score_pos_freq': 1.5/turn, 'distinct_letters': 1.2}))
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

        wordle_solver.process_guess(guess=guess, response=list(raw_response))

        turn += 1