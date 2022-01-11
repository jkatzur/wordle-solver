from typing import List
import random
from wordfreq import get_frequency_dict

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
        self.possible_words = self.possible_words()
        
    # Return list of all possible words of n_letter length as a dict with wordfreq
    def possible_words(self) -> List[int]:
        freq_dict = get_frequency_dict('en', wordlist='best')
        n_letter_words = []
        for w in freq_dict.items():
            if len(w[0]) == self.n_letters and w[0].isalnum(): #removes non-alpha words like don't
                n_letter_words.append(w)
        return n_letter_words
    
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

        self.possible_words = [w for w in self.possible_words if self.word_in(w)]

    # Determines if a given word matches all conditions in current state
    # This is a naive implementation. Could improve by only evaluating new conditions
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
    
    # Next guess currently just returns the highest frequency next guess
    # This is the method that is overridden in more advanced solvers
    def next_guess(self) -> str:
        return self.possible_words[0][0]


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
        # Input guess
        while True:
            guess = input(f"Turn {turn}. Input your guess: {'' : >5}").lower()
            if guess.isalnum and len(guess) == n_letters:
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

        print(f"\nThat response reduces possible matched words to {len(wordleSolver.possible_words)}")
        print(f"Top guess based on frequency is: {wordleSolver.possible_words[0][0]}")

        # Would you like to see more
        while True:
            see_top = input(f"Would you like to see the top 20 possible words? Y(es) or N(o)? {'' : >3}").upper()
            if see_top == 'Y' or see_top == 'N':
                break
            else:
                print(f"Sorry, try again.")

        if see_top == 'Y':
            print(f"\nTop 20 suggested guesses are:")
            for w in wordleSolver.possible_words[0:20]:
                print(f"Word: {w[0]}, Freq: {w[1]}")
            print("\n")

        turn += 1