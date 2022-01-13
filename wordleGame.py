from wordfreq import get_frequency_dict
import random

class wordleGame:
    def __init__(self, n_letters: int, random_word: bool = True, starter_word: str = ''):
        self.n_letters = n_letters
        self.random_word = random_word
        self.word = self.seed_word(starter_word)
        self.turn = 0
    
    def seed_word(self, starter_word: str):
        if self.random_word:
            freq_dict = get_frequency_dict('en', wordlist='best')
            n_letter_words = []
            for w in freq_dict.items():
                if len(w[0]) == self.n_letters and w[0].isalpha(): #removes non-alpha words like don't
                    n_letter_words.append(w)
            return n_letter_words[random.randint(0, 10000)][0] # pick one of the 10,000 most common words for this length
        else:
            return starter_word

    def respond_guess(self, guess: str) -> dict:
        self.turn += 1
        win = False
        response = ''
        for i, l in enumerate(guess):
            if l == self.word[i]:
                response += ('+')
            elif l in self.word:
                response += ('-')
            else:
                response += ('_')

        if sum([1 for r in response if r == '+']) == len(response):
            win = True
        
        return {"win": win, "turn": self.turn, "response": response}

# For when you are running a game via the command line
if __name__ == '__main__':
    # Pick a length of game
    while True:
        try: 
            n_letters = int(input("What length word Wordle to play? Enter a number 2 through 15.\t"))
            if 2 <= n_letters <= 15:
                break
            else:
                print("Pick a number 2 to 15")
        except ValueError:
            print("Please enter an integer from 2 to 15")

    print(f"Input: {n_letters}")

    # Play against a randomly word or a human generated starter word?
    while True:
        random_input = input("Play against a randomly generated word or enter your own. Enter [R]andom or [M]y own.\t").upper()
        if random_input == 'R':
            random_word = True
            break
        elif random_input == 'M':
            random_word = False
            break
        else:
            print("Please enter R for Random word or M for My own word")

    # If they picked a starter word ask for it
    if not random_word:
        while True:
            starter_word = input("Pick your starter word. Make sure it is {n_letters} characters\t")
            if len(starter_word) == n_letters:
                break
            else:
                print("Try again. Pick a starter word that is {n_letters} characters")
    else:
        starter_word = ''

    # Setup the wordle game
    wordleGame = wordleGame(n_letters=n_letters, random_word=random_word, starter_word=starter_word)
    game_on = True
    turn = 1

    print(f"\n---- Starting wordle game with {n_letters} letter word ----\n")
    
    # Core game loop
    while game_on:
        # Input guess
        while True:
            guess = input(f"Turn {turn}. Input guess: {'': >5}").lower()
            if guess.isalpha and len(guess) == n_letters:
                break
            elif guess.isalpha and len(guess) != n_letters:
                print(f"That word is {len(guess)} characters, not {n_letters}. Try again")
            else:
                print(f"That word includes a non-alpha character")

        response = wordleGame.respond_guess(guess=guess)
        
        if response['win']:    
            print(f"\n!!!! That's correct! Game over! You won in {response['turn']} turns! !!!!")
            game_on = False
        else:
            print(f"Response: {response['response'] : >{16+n_letters}}\n")
            turn += 1