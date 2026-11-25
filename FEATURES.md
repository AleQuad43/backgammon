# Backgammon — the features we keep

The list for the clean-up: everything Quad has asked for across our chats, gathered from the notes Claude kept. If it's
not on this list, it goes (or comes back only when asked for). Strike out or correct anything that's wrong before the
rewrite starts.

## The idea
- Free backgammon for about ten friends. No ads, nobody pays, no groups: everyone plays everyone, one Elo ranking.
- Turn-based. You can open any game and watch live while the other player moves. No pushy notifications.
- Laid-back, soothing, easy on the eyes. Real materials: wood, bone, wear. Middle Eastern touches (shesh besh).
- Installable web app (GitHub Pages), Firebase for accounts and shared games.

## Accounts
- Name, email and a 4-digit PIN. Forgot it: Firebase's reset email (new PIN typed twice).
- The first account (Quad) is admin and sees everyone's email.

## Home
- No tab bar, no drill-in/back navigation.
- Friends as floating checkers (orbs); height = Elo. Pull them around: water/air physics (Quad's tuned values).
- Sky follows the time of day (aurora pools, Bubble app feel).
- Your-turn signal: that friend's checker slowly flips with a lit edge.

## Your checker (avatar)
- The checker workshop is the avatar picker: material (wood, marble, bone, bakelite) × tone × face × inlay × age/wear.
- A turning checker always shows its thickness (the wall), from every side.

## A friend's card
- Their checker, name, Elo and rank ("2nd of 5").
- Your record together in matches won (no win rate, no gammon stats).
- The match in progress as a small real board; tap it to play.
- Past matches as green/red tiles: score, "to N", start–end day and time.
- No match on: set one up here (below).
- Your own card: same layout, plus sign out.

## Starting a match (the invitation)
- On the friend's card: points to win on a sliding selector (1, 3, 5, 7, 9, 11, 15), Pip counts on/off, your colour
  (white or black: the two checkers turning like coins on a strip of wood), then Play. Last choices remembered.
- Starting the match throws your opening die.
- The friend gets an invitation card (café note, a greeting from one of five backgammon cultures): who, how long, the two
  checkers. They may swap the colours once, then accept. After that the colours stay for the whole match.
- Both phones show each player in their own colour.

## The board
- Landscape. Wooden board, rail on one side (switchable), score on the sky, names and avatars, match length.
- Board sky fixed at sunset per time of day; turn change = the pools rotate half a turn.
- Dice: tap or flick to throw, real physics, result obvious.
- Moves: tap a checker = higher die first (tap the dice to swap order); drag lights up only reachable points; next-door
  points warn and snap to the good one. Highlights in sky colours, lifted above the board.
- Undo: drag a moved checker back (or double tap it). No Undo/Done buttons.
- End your turn: flick the dice toward the other player.
- Forced moves play themselves (only one way to play, or none). *(Check: keep this?)*
- No automatic throws. Each player throws their own dice, also from the bar or shut out. Turns alternate one for one;
  the race roll-out is the only exception.
- Race roll-out: when it's a pure race, both may agree to roll it out automatically; the other phone replays it.
- Missed turns replay move by move with a short caption, then a summary. Tap to skip.

## Doubling and giving up
- Drag the red cube from the rail onto the board to offer (it turns over, ×2).
- Receiving: sky turns to you, big ×2; tap = take, hold and slide = give up.
- Give up the match: pinch the board shut with two fingers; only then it asks "Give up the match?".

## Rules (the Israeli friend's)
- Single 1, gammon (mars) 2, backgammon 3.
- No doubling while either player is one point from winning. Cube up to 64.
- Last game's winner starts the next game; opening roll only for a match's first game.

## End of a game / match
- Café-note card with a phrase from one of five cultures (Turkish, Levantine Arabic, Persian, Greek, Hebrew), both
  players' checkers spinning on the paper.
- A finished game stays finished; a phone that missed the end sees it before the next game. No spoilers: home and Elo
  hold the result back until you've seen it.
- Match end: saved once; Elo (FIBS-style, weighs match length) updates for everyone.

## Later (agreed, not built)
- Board personalization ("who brings the board"), paired checker sets.
- Pace of play: gentle nudges at day 1 and 3, claim the game at day 7. Notifications (gentle).
- One-tap chat / reactions. Dice calls after a roll (shesh besh, dubara…).
- Replay speed slider for roll-outs. Stats and move grading.

## Test kit (stays)
- design/tests: two-phone scenarios, whole-match simulator, end-of-game and fixes pages, static check. Run before
  every ship.
