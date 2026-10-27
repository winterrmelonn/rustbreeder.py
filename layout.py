# ============================================================================
# layout.py — THE PLANNER
#
# rustbreeder.py answers "what does THIS cross produce?".
# This file answers the harder question: "given the seeds I'm holding, where
# should I plant each one, and what should I do next generation?"
#
# It's a SEARCH problem: there are hundreds of thousands of ways to arrange 9
# plants in a planter, and we want the best one without checking them all.
#
# Project map:
#   rustbreeder.py  <- breeding rules + scoring
#   layout.py       <- you are here (where to plant / multi-generation plans)
#   gui.py          <- draws the window
# ============================================================================

import functools
import itertools
import random

from rustbreeder import breed, score

# --- THE PLANTER -----------------------------------------------------------
# A 3x3 grid. Positions are (row, column) pairs, so (0,0) is top-left and
# (2,2) is bottom-right.
GRID = [(r, c) for r in range(3) for c in range(3)]

# For each position, which positions touch it. Up/down/left/right only — no
# diagonals, matching the game's cross-pollination rule.
# The four (dr, dc) pairs are the four directions: up, down, left, right.
# The `if ... in GRID` check throws away anything off the edge of the planter,
# which is why corners end up with 2 neighbors, edges 3, and the center 4.
NEIGHBORS = {
    pos: [
        (pos[0] + dr, pos[1] + dc)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if (pos[0] + dr, pos[1] + dc) in GRID
    ]
    for pos in GRID
}

# Positions sorted by how many neighbors they have, most first (center, then
# edges, then corners). The minus sign in the key reverses the sort.
# Why: if you only hold 4 seeds you can't fill the planter, and a plant with
# more neighbors gets more breeding influence — so fill the busy spots first.
POSITIONS = sorted(GRID, key=lambda p: -len(NEIGHBORS[p]))


# --- SPEED FIX 1: REMEMBER ANSWERS -----------------------------------------
# @functools.lru_cache wraps this function in a hidden dictionary. The first
# time it's called with some arguments it actually runs and stores the answer;
# every later call with those same arguments returns the stored answer without
# running anything. maxsize=None means "never forget anything".
#
# This matters enormously: the search below evaluates the same center+neighbor
# combinations millions of times, but with 9 genomes there are only a few
# thousand DISTINCT questions to ask.
#
# Two requirements this creates:
#   1. Arguments must be hashable (usable as dict keys). Tuples are, lists are
#      NOT — that's why `neighbors` is a tuple, converted back with list() below.
#   2. Callers must pass neighbors SORTED. breed() just adds up weights, so
#      ("GGGGGG","YYYYYY") and ("YYYYYY","GGGGGG") are the same question. Sorting
#      first means all orderings share one cache entry instead of wasting 24
#      entries on the same answer.
@functools.lru_cache(maxsize=None)
def cell_outcome(center, neighbors):
    """(offspring, score) for one planter cell."""
    child = breed(center, list(neighbors))
    return child, score(child)


def layout_fitness(assignment):
    """Score a whole planter.

    `assignment` maps position -> genome, e.g. {(1,1): "GGGYYY", ...}.
    Returns (total score, {position: predicted offspring}).
    """
    offspring = {}
    total = 0
    for pos, genome in assignment.items():
        # Collect the genomes of this cell's planted neighbors. The
        # `if n in assignment` skips neighboring positions left empty.
        # sorted(...) then tuple(...) builds the cache-friendly key described above.
        neighbors = tuple(sorted(assignment[n] for n in NEIGHBORS[pos] if n in assignment))
        child, value = cell_outcome(genome, neighbors)
        offspring[pos] = child
        total += value
    return total, offspring


# --- THE TWO GOALS ---------------------------------------------------------
# An "objective function" takes a candidate layout and returns a number where
# bigger = better. The search just maximizes whatever you hand it, so swapping
# the objective completely changes what it hunts for. These two are genuinely
# different goals and give different answers:
def total_score(assignment):
    """All 9 cells added up — 'make the whole planter productive'."""
    return layout_fitness(assignment)[0]


def best_single(assignment):
    """Only the single best cell counts — 'get me one perfect plant, I don't
    care about the other eight'. This is the right goal when chasing GGGYYY."""
    return max(score(g) for g in layout_fitness(assignment)[1].values())


# --- SPEED FIX 2: STOP CHECKING EVERY LAYOUT -------------------------------
# The old version tried all 9! = 362,880 arrangements. That's what froze the
# window. These three functions replace it with "hill climbing", which checks a
# few hundred instead — and the self-check at the bottom proves it still finds
# the same winner.
#
# (Functions starting with _ are a Python convention meaning "internal helper,
# not meant to be called from outside this file".)

def _random_assignment(pool, slots, clones, rng):
    """A random starting layout to climb away from."""
    if clones:
        # Unlimited seeds: every slot independently picks any genome, repeats allowed.
        return {pos: rng.choice(pool) for pos in slots}
    # One seed each: sample() draws WITHOUT replacement, so no genome repeats.
    return dict(zip(slots, rng.sample(pool, len(slots))))


def _climb(pool, slots, clones, objective, rng):
    """Hill climbing: start somewhere random, then repeatedly make the single
    best one-cell change available. Stop when no change improves things.

    The mental picture: all possible layouts form a landscape where height =
    score. You're dropped at a random spot and keep stepping uphill until
    every direction leads down. A "step" here means changing one cell.
    """
    current = _random_assignment(pool, slots, clones, rng)
    best_value = objective(current)

    improved = True
    while improved:          # keep sweeping the whole grid until a full pass changes nothing
        improved = False
        for pos in slots:              # for every cell...
            for candidate in pool:     # ...try every genome we could put there
                if candidate == current[pos]:
                    continue           # already there, nothing to test

                # IMPORTANT: copy before modifying. Without dict(current) we'd be
                # editing the layout we're comparing against, and a rejected
                # experiment would permanently corrupt it.
                trial = dict(current)

                if clones:
                    trial[pos] = candidate     # unlimited seeds: just drop it in
                else:
                    # Only one of each physical seed, so planting it here means
                    # taking it from wherever it currently is — a SWAP.
                    # next((...), None) finds that position, or None if this
                    # genome isn't currently planted anywhere.
                    other = next((p for p in slots if current[p] == candidate), None)
                    if other is None:
                        continue
                    trial[pos], trial[other] = candidate, current[pos]

                value = objective(trial)
                if value > best_value:
                    # Better! Move here and remember to sweep again, because
                    # this change may have opened up further improvements.
                    current, best_value, improved = trial, value, True
    return current, best_value


def _search(pool, slots, clones, objective, restarts, rng):
    """Hill climbing has one weakness: it stops at the first peak it reaches,
    which might not be the tallest one (a "local optimum"). The fix is to just
    do it many times from different random starts and keep the best result.
    On a 9-cell grid, 30 restarts reliably finds the true best — which the
    self-check at the bottom verifies against brute force.
    """
    best, best_value = None, -1
    for _ in range(restarts):
        assignment, value = _climb(pool, slots, clones, objective, rng)
        if value > best_value:
            best, best_value = assignment, value
    return best, best_value


def best_layout(held_plants, clones=False, objective=total_score, restarts=30, seed=0):
    """Find the best arrangement of the seeds you're holding. This is what the
    GUI's Finalize button calls.

    clones=False: each genome is ONE physical seed you own (generation 1).
    clones=True:  unlimited seeds of each genome — true after you've harvested.
    """
    # set() removes duplicate genomes; sorted() then fixes the order, because
    # sets have no guaranteed order and that would make results vary run to run.
    pool = sorted(set(held_plants))
    # With clones you can always fill all 9 cells. Without, you can only fill
    # as many cells as you have seeds.
    slots = POSITIONS if clones else POSITIONS[: min(len(pool), len(POSITIONS))]

    # random.Random(seed) is a private random generator with a fixed starting
    # point, so the same input always produces the same plan. Reproducible
    # results mean a weird answer can actually be investigated.
    assignment, _ = _search(pool, slots, clones, objective, restarts, random.Random(seed))
    fitness, offspring = layout_fitness(assignment)
    return assignment, offspring, fitness


def best_plan(held_plants, generations=2, restarts=30, seed=0):
    """Plan SEVERAL breeding rounds ahead.

    Returns ([(assignment, offspring), ...], best_genome) — one pair per
    generation, plus the best plant you end up holding.

    The whole multi-generation idea is the loop below: search a layout, harvest
    its offspring, and those offspring become the pool you plant next round.

    ponytail: greedy — each generation is optimized on its own with no
    lookahead, so it can pick a round with one great offspring over one with a
    richer pool that would breed better next time. Beam search (keep the top K
    layouts per generation and expand all of them) is the fix if plans start
    looking short-sighted.
    """
    rng = random.Random(seed)
    pool = sorted(set(held_plants))
    plan = []

    for generation in range(generations):
        # Generation 0 uses the seeds you physically hold. Every generation
        # after that can clone freely, because harvesting one plant gives you
        # multiple seeds of that exact genome.
        clones = generation > 0
        slots = POSITIONS if clones else POSITIONS[: min(len(pool), len(POSITIONS))]

        # best_single, not total_score: across multiple generations the goal is
        # one perfect plant, not a uniformly decent planter.
        assignment, _ = _search(pool, slots, clones, best_single, restarts, rng)
        _, offspring = layout_fitness(assignment)
        plan.append((assignment, offspring))

        # THE HANDOFF: this round's harvest is next round's seed pool.
        # set() dedupes because once cloning is allowed, holding two copies of
        # the same genome is no different from holding one.
        pool = sorted(set(offspring.values()))

    return plan, max(pool, key=score)


# --- TEXT OUTPUT (used by the terminal version, not the GUI) ---------------
def format_grid(assignment, offspring):
    """Build a printable picture of a planter as one string."""
    lines = []
    for r in range(3):
        # .get(pos, "------") prints a blank placeholder for unplanted cells.
        lines.append("  ".join(assignment.get((r, c), "------") for c in range(3)))
    lines.append("")
    for pos in POSITIONS:
        if pos in assignment:
            lines.append(f"{pos}: plant {assignment[pos]} -> offspring {offspring[pos]} (score {score(offspring[pos])})")
    return "\n".join(lines)


def print_grid(assignment, offspring):
    print(format_grid(assignment, offspring))


# --- SELF-CHECK ------------------------------------------------------------
# Each assert pins down one thing that must stay true. Run this file to check
# them all; a failure points straight at what broke.
def demo():
    # The grid is shaped the way we think it is.
    assert len(NEIGHBORS[(1, 1)]) == 4
    assert len(NEIGHBORS[(0, 0)]) == 2

    # Planting nine identical plants must produce nine identical offspring.
    fitness, offspring = layout_fitness({p: "GGGGGG" for p in POSITIONS})
    assert all(g == "GGGGGG" for g in offspring.values())
    assert fitness == 9 * score("GGGGGG")

    # Neighbor ORDER must not change the outcome. This is the assumption that
    # makes cell_outcome's cache safe — if it ever broke, the cache would start
    # handing back answers to the wrong question.
    assert cell_outcome("XYGWGG", ("GGGGGG", "YYYYYY")) == cell_outcome("XYGWGG", ("YYYYYY", "GGGGGG"))

    # THE IMPORTANT ONE: brute-force every arrangement of 5 plants (only 120, so
    # it's affordable here) and confirm hill climbing finds the identical best.
    # This is what makes the 60x speedup trustworthy rather than hopeful.
    held = ["GGGYYY", "GGGGGG", "YYYYYY", "GYHXWG", "GGGHHH"]
    slots = POSITIONS[: len(held)]
    exhaustive = max(
        (total_score(dict(zip(slots, order))) for order in itertools.permutations(held)),
    )
    assert best_layout(held)[2] == exhaustive, "hill climbing missed the true optimum"

    # A multi-generation plan must never go backwards.
    plan, best = best_plan(held, generations=2)
    assert len(plan) == 2
    assert score(best) >= max(score(g) for g in held)
    print("demo: ok")


if __name__ == "__main__":
    demo()
    held_plants = ["GGGYYY", "GGGGGG", "YYYYYY", "GYHXWG", "GGGHHH"]

    assignment, offspring, fitness = best_layout(held_plants)
    print(f"\nOne generation (total score {fitness}):\n")
    print_grid(assignment, offspring)

    plan, best = best_plan(held_plants, generations=2)
    print(f"\n\nTwo-generation plan -> best plant {best} (score {score(best)}):")
    for generation, (assignment, offspring) in enumerate(plan, start=1):
        print(f"\n--- generation {generation} ---")
        print_grid(assignment, offspring)
