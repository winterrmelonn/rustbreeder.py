# ============================================================================
# rustbreeder.py — THE GENETICS ENGINE
#
# This is the bottom layer of the project. Nothing here knows about grids or
# windows; it only answers two questions:
#   1. breed()  — if I plant THIS next to THOSE, what offspring do I get?
#   2. score()  — how good is a given plant?
# Everything else in the project is built on top of these two.
#
# Project map:
#   rustbreeder.py  <- you are here (breeding rules + scoring)
#   layout.py       <- uses this to decide WHERE to plant things
#   gui.py          <- uses both to draw the window
# ============================================================================

# Salutations.
# Today(s), we'll be replicating a site called rustbreeder.com.
# In Rust, there are advantageous teas that can be made with berries. By crossbreeding berry seeds, you can obtain seeds with faster growing times and greater yields.
# Each seed has 6 gene slots. The goal here: grow our own GGGYYY clone.

# The five possible genes. G=Growth, Y=Yield, H=Hardiness, W=Water, X=Nothing.
GENES = "GYHXW"

# How strongly each gene fights to be inherited.
# Good genes (GYH) weigh 3, bad genes (WX) weigh 5 — bad genes are STICKIER,
# which is why junk is so hard to breed out. The 3-vs-5 ratio is what creates
# the rule "two matching good neighbors (3+3=6) beat one bad gene (5)".
WEIGHTS = {"G": 3, "Y": 3, "H": 3, "W": 5, "X": 5}


# --- THE CORE RULE ---------------------------------------------------------
# One gene slot, one decision. Every other prediction in this project is just
# this function called over and over.
#
# How it works: the neighbors "vote" for their gene at this slot, with each
# vote worth that gene's WEIGHT. The heaviest neighbor gene then challenges
# the center plant's own gene. The center only loses if the challenger is
# strictly heavier — so TIES GO TO THE CENTER (it keeps what it had).
def breed_slot(center_gene, neighbor_genes):
    # Start every gene at zero weight, then add up the neighbors' votes.
    slot_weights = {g: 0 for g in GENES}
    for gene in neighbor_genes:
        slot_weights[gene] += WEIGHTS[gene]

    # max(dict, key=dict.get) returns the KEY with the highest value — i.e. the
    # single gene with the most total weight behind it. Note weights only stack
    # between IDENTICAL genes: two neighbors with G and Y don't combine into 6,
    # they stay as two separate 3s.
    winning_neighbor_gene = max(slot_weights, key=slot_weights.get)
    neighbor_slot_weight = slot_weights[winning_neighbor_gene]
    center_slot_weight = WEIGHTS[center_gene]

    if neighbor_slot_weight > center_slot_weight:
        return winning_neighbor_gene  # neighbors overpowered the center
    return center_gene                # center held on (including on a tie)


# --- ONE WHOLE PLANT -------------------------------------------------------
# A plant is 6 independent slots, so predicting a full offspring is just
# breed_slot() six times. Slot 0 of the center only ever competes with slot 0
# of the neighbors — genes never move sideways between slots.
def breed(center_plant, neighbor_plants):
    offspring = ""
    for slot in range(6):
        center_gene = center_plant[slot]
        # Pull out every neighbor's gene at THIS slot position only.
        neighbor_genes = [plant[slot] for plant in neighbor_plants]
        offspring += breed_slot(center_gene, neighbor_genes)
    return offspring


# --- SELF-CHECK ------------------------------------------------------------
# Running this file executes these asserts first. If a future change breaks the
# breeding rules, the program dies here with a clear error instead of silently
# giving wrong predictions for the rest of the project.
def demo():
    # one weak (3) neighbor can't beat a strong (5) center gene -> center holds
    assert breed_slot("X", ["G"]) == "X"
    # two matching good neighbors (3+3=6) beat one bad center gene (5) -> neighbor wins
    assert breed_slot("X", ["G", "G"]) == "G"
    # mixed neighbor genes never combine -> center still holds
    assert breed_slot("X", ["G", "Y"]) == "X"
    # all-G neighbors pull any center plant fully green
    assert breed("XYGWGG", ["GGGGGG", "GGGGGG"]) == "GGGGGG"
    print("demo: ok")


# --- SCORING ---------------------------------------------------------------
# Turns a genome into a single number so plants can be ranked and compared.
# This is OUR opinion of "good", not a game rule — tune the numbers here if you
# decide you value something differently.
def score(single_plant):
  count_G = single_plant.count("G")
  count_Y = single_plant.count("Y")
  count_H = single_plant.count("H")
  # G and Y are worth 10 each, H only 2, W and X are worth nothing.
  # The min(G, Y) * 5 at the end is a BALANCE BONUS: it rewards having both
  # instead of six of one. GGGYYY scores min(3,3)=3 -> +15, while GGGGGG
  # scores min(6,0)=0 -> +0. That's what makes GGGYYY the target.
  return (count_G * 10) + (count_Y * 10) + (count_H * 2) + (min (count_G, count_Y) * 5)


# --- CLI WALKTHROUGH -------------------------------------------------------
# Everything below only runs when you execute THIS file directly
# (python3 rustbreeder.py). The __name__ check is what makes that work:
# Python sets __name__ to "__main__" for the file you run, but to the module
# name ("rustbreeder") when another file imports it. Without this guard, the
# input() loop below would fire every time gui.py or layout.py imported
# score() — the window would hang forever waiting for terminal input.
if __name__ == "__main__":
    demo()

    # Step 1: Create User Input (you need to have seeds to crossbreed after all)

    user_input_plants = []
    while True:
        user_input = input("Add gene:").upper()
        letters_in_genepool = True
        for letter_input in user_input:
          if letter_input not in "GYHXW":
            letters_in_genepool = False
        if not letters_in_genepool:
          print("Invalid gene.")
          continue
        if user_input == "":
         print("Entered genes:", user_input_plants)
         break          # empty input is the signal for "done entering"
        if len(user_input) != 6:
         print("Invalid gene.")
         continue
        user_input_plants.append(user_input)

    # The user inputs gene combinations that are added to a table.
    # I've coded in checks to ensure user input is 6 letters long and follows Rust's gene conventions. (GYHWX, representing Growth, Yield, Hardiness, Water, and Nothing, respectively.)
    # User inputs that fail the checks are not added to the table. Lowercase inputs are automatically uppercased.

    # Step 2: Counting & Scoring

    for single_plant in user_input_plants:
      print(single_plant, score(single_plant))

    # Some genes, like Growth and Yield, are more desirable than others: let's weigh each gene; a high score for Growth and Yield genes, zero score for Water and Nothing genes, and weigh Haridiness between the two.
    # We use the minimum function to accomodate balance. We want a balance of Growth and Yield genes.
    # The ideal plant (3G, 3Y) will return a minimum of 3.
    # Unbalanced plants, (6G, 0Y) will return a minimum of 0. We want the balance to affect plant rankings; so multiply this minimum value by 5.

    # Classic "find the biggest" loop: hold the best seen so far, replace it
    # whenever something beats it. Starting at -1 guarantees the first plant wins.
    best_plant = ""
    best_plant_score = -1
    current_score = 0

    for single_plant in user_input_plants:
      current_score = score(single_plant)
      if current_score > best_plant_score:
        best_plant_score = current_score
        best_plant = single_plant
    print("Best plant:", best_plant, "with score:", best_plant_score)

    # Step 3: Predicting a Gene
    # Rust genetics sort individually. Think of each of the six genes as a slot.
    # We can calculate each slot outcome of a plant given its "slot neighbors." (the gene of a neighboring plant(s) at that slot)

    # Worked example: center X (weight 5) vs neighbors G,Y,Y,Y.
    # The three Ys stack to 9, which beats 5, so Y wins this slot.
    print("Slot winner:", breed_slot("X", ["G", "Y", "Y", "Y"]))

    # Step 4: Predicting a Plant
    # Same idea, run across all 6 slots of a real center plant and its neighbor plants.

    center_plant = "XYGWGG"
    neighbor_plants = ["GGGGGG", "GGGGGG"]
    print("Offspring:", breed(center_plant, neighbor_plants))
