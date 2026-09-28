#!/usr/bin/env python3
"""The three posts written on 2026-09-28, each from a bug that actually happened here.

    python3 tools/posts-2026-09-28.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
np = import_module("new-post".replace("-", "_")) if False else None

# new-post.py has a hyphen, so import it by path.
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "newpost", os.path.join(os.path.dirname(os.path.abspath(__file__)), "new-post.py"))
NP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(NP)

DATE_ISO, DATE_TXT = "2026-09-28", "September 28, 2026"

P1 = {
    "slug": "test-modelled-open-sky",
    "date_iso": DATE_ISO, "date_txt": DATE_TXT,
    "title": "The Test Was Modelling a Game We Had Stopped Running",
    "sub": "A ceiling constant clipped every jump from high ground, and the gate that existed to "
           "catch exactly that reported the levels were fine",
    "desc": "A one-line ceiling made six of seven levels uncrossable. The hard gate never saw it, "
            "because it computed jump arcs in open sky. What it costs when a test models the "
            "physics instead of reading it.",
    "alt": "Diagram: a 136px jump against 29px of headroom under a ceiling at y=80",
    "next_slug": "railway-up-working-directory",
    "next_title": "What railway up Actually Uploads",
    "body": """
                    <p>Players could fly over our platformer. The puff mechanic that was supposed to rescue a jump had become a way to cruise above the whole stage, so we did two things about it: made holding the puff progressively more expensive, and added a ceiling.</p>

                    <p>The ceiling was one line. <code>const ROOF = 80;</code> It applied to all vertical motion.</p>

                    <p>A week later, six of the seven levels could not be finished.</p>

                    <h2>The arithmetic nobody did</h2>

                    <p>A full jump in this game rises <code>JUMP_V&sup2; / (2 &times; GRAV)</code>, which is 790&sup2; / 4600, which is 136 pixels. The tallest platform in any level sits at y=147, and the character is 38 pixels tall, so standing on it his head is at y=109.</p>

                    <p>109 minus 80 is 29.</p>

                    <p>So a jump taken from the upper half of any stage was cut to a fifth of its height and landed short. Not for bots. For anybody. The ceiling was doing to the player exactly what it was meant to do to the exploit, and nobody had subtracted the two numbers.</p>

                    <p>It did not present as a ceiling bug. It presented as <em>the levels are too hard</em>, which is the kind of complaint you answer by moving platforms around. We moved platforms around three times before measuring.</p>

                    <h2>The part that actually matters</h2>

                    <p>We had a gate for this. A script called <code>reach.mjs</code> whose entire job was to answer &ldquo;can every gap be crossed at all&rdquo;, run on every change, pulling the movement constants straight out of the game so it could never disagree with them.</p>

                    <p>It said every gap was crossable. It said that the whole time.</p>

                    <p>Because it computed the jump as a parabola under constant gravity, took off, peaked, landed. Which is what the game did until the day it did not. The gate modelled open sky. It was computing the flight of a game we had stopped running, and it was doing it with the real <code>GRAV</code> and the real <code>JUMP_V</code>, which is what made it so convincing.</p>

                    <p>The second harness was worse. A difficulty bot drove the actual game code in a sandbox, and its sandbox carried <code>ROOF: 80</code> as a hardcoded literal. So when the game's value changed, the bot went on scoring a game nobody was playing, and reported a baseline it met.</p>

                    <h2>Teaching the gate about the ceiling</h2>

                    <p>The fix to <code>reachFor()</code> is eight lines: rise freely until the head reaches the ceiling, lose the rest of the climb, then fall.</p>

                    <pre><code>const freeRise = (v * v) / (2 * GRAV);
const headroom = (fromPlatY - NUG_H) - ROOF;
if (freeRise &lt;= headroom) return MOVE * ((v + Math.sqrt(disc)) / GRAV);
const vAtRoof = Math.sqrt(Math.max(0, v * v - 2 * GRAV * headroom));
const tUp = (v - vAtRoof) / GRAV;
const drop = headroom + dy;
if (drop &lt; 0) return -1;
return MOVE * (tUp + Math.sqrt((2 * drop) / GRAV));</code></pre>

                    <p>Then we put the broken value back to see whether the gate would now fail. It named four impassable gaps, at x=730, x=1130, x=1550 and x=1130 on four different levels. One of those matched, to the pixel bucket, where the bot had been dying forty times out of forty.</p>

                    <p>That last step is the one worth stealing. A gate you have only ever seen pass is not a gate yet. It is a script that has never been asked a hard question. Break the thing on purpose, watch the check go red, put it back.</p>

                    <h2>Which of the two fixes was even doing anything</h2>

                    <p>Since we had changed two things at once, we swept them independently against the same bot:</p>

                    <table>
                      <thead><tr><th></th><th>ceiling on</th><th>ceiling off</th></tr></thead>
                      <tbody>
                        <tr><td>expensive puff</td><td>0 wins</td><td>6</td></tr>
                        <tr><td>flat puff</td><td>0 wins</td><td>40</td></tr>
                      </tbody>
                    </table>

                    <p>The cost alone took the exploit from 40 wins to 6, an 85% cut, with no ceiling in play at all. A full meter now buys about 1.07 seconds of float and carries roughly 350 pixels of a 2,700-pixel level. That is a rescue, not a flight.</p>

                    <p>So the ceiling was never load-bearing. It was a second fix for a problem the first fix had already solved, and it was breaking the game to do it. It is now set above the highest point any jump can reach, where it can still catch something that throws the player off-screen and can never touch an ordinary jump.</p>

                    <h2>What we took from it</h2>

                    <p>Three things, in the order they cost us time.</p>

                    <p><strong>A test that re-implements behaviour will eventually test something else.</strong> Ours pulled the real constants, which felt rigorous, and that is exactly why nobody suspected it &mdash; it was wrong in its model, not in its inputs. Where you can, drive the real code path. Where you cannot, write down which behaviours you are approximating, because that list is the list of ways the test can quietly stop being true.</p>

                    <p><strong>A duplicated constant is a future disagreement with a date on it.</strong> Slice it out of the source or do not have it.</p>

                    <p><strong>Change one thing.</strong> Had we shipped the puff cost by itself, the measurement would have said 40 to 6 immediately, the ceiling would never have been written, and none of this would have happened.</p>

                    <p><em>We build games and tools, and we write up the bugs that taught us something. <a href="services.html">Rebel Studios</a>.</em></p>
""",
}

P2 = {
    "slug": "railway-up-working-directory",
    "date_iso": DATE_ISO, "date_txt": DATE_TXT,
    "title": "What railway up Actually Uploads",
    "sub": "Not your commit. The folder you are standing in &mdash; including whatever you have not "
           "committed yet",
    "desc": "Nine commits sat invisible to users for seven hours while every deploy reported "
            "success. Two facts about Railway deploys worth knowing before you automate one.",
    "alt": "Diagram: git push reaches nothing, railway up uploads the working directory",
    "next_slug": "stale-base-dropped-commits",
    "next_title": "Every Test Passed and Four Commits Were Gone",
    "body": """
                    <p>One morning our site was nine commits behind. The overnight worker had committed and pushed all of them. The push succeeded. The tests passed. The deploy step reported success. Users had seen none of it for seven hours.</p>

                    <p>Two facts explain it, and both are easy to get wrong.</p>

                    <h2>A push deploys nothing unless something is listening</h2>

                    <p>Our service had no source connected. No repository, no image. You can see it plainly in the config &mdash; there is simply no <code>source</code> key:</p>

                    <pre><code>{"config": {
  "build":  {"builder": "RAILPACK"},
  "deploy": {"runtime": "V2"},
  "networking": {"customDomains": {"example.com": {}}}
}}</code></pre>

                    <p>Every deploy that had ever happened was somebody typing <code>railway up</code>. That works perfectly and it is invisible: the service is live, the domain resolves, health checks pass. Nothing about the running site tells you that pushing to the default branch does not reach it.</p>

                    <p>When the automation that was calling <code>railway up</code> stopped, there was no second mechanism, and nothing reported the absence. A deploy that never starts produces no failed build to notice. Our deployment list showed the last success and then nothing at all &mdash; not one <code>FAILED</code>, not one <code>CRASHED</code>. Just a gap.</p>

                    <h2>It uploads the folder, not the commit</h2>

                    <p>This is the one to internalise before you automate anything. <code>railway up</code> tars up the working directory and sends that. Not <code>HEAD</code>. Not the branch. The directory, as it exists on disk, at that moment.</p>

                    <p>Most of the time the difference does not bite, because you deploy from a clean tree. It bites when a human is mid-experiment in that folder, or when a script runs on a timer in a directory somebody else is also using. Then you ship a debug constant, a commented-out guard, a half-finished migration &mdash; something nobody wrote down, nobody reviewed, and which does not correspond to any commit you can go back and read.</p>

                    <p>Our first instinct was to point a five-minute watcher at the main checkout. That would have been a machine that publishes whatever is lying around, every five minutes, forever.</p>

                    <h2>What we did instead</h2>

                    <p>Connecting the repository is the correct fix, and we could not do it &mdash; the GitHub app was not authorised on a private repo and that needs a browser and a human. So the stand-in deploys from its own clone, which exists for nothing else:</p>

                    <pre><code>cd ~/deploy-mirror
git fetch -q origin master
git reset -q --hard origin/master   # safe here: this tree holds no work
railway up --service web --detach</code></pre>

                    <p>The <code>reset --hard</code> is only acceptable because that directory can never contain anything a person cares about. Point the same three lines at a working checkout and you have written a tool that destroys uncommitted work on a timer.</p>

                    <h2>Then wait for the thing you actually want</h2>

                    <p>The last piece matters more than the deploy. <code>railway up --detach</code> returning zero means the upload was accepted. It does not mean the new code is serving.</p>

                    <p>So we put a build identifier in the app, returned from its health endpoint, and the deploy script does not consider itself finished until that string changes:</p>

                    <pre><code>for i in $(seq 1 36); do
  sleep 10
  got=$(curl -s "$HEALTH?cb=$RANDOM" | grep -oE '"build":"[^"]+"' | cut -d'"' -f4)
  [ "$got" = "$want" ] &amp;&amp; { echo "LIVE: $want"; exit 0; }
done
echo "WARNING: uploaded but '$want' is not serving after 360s"
exit 1</code></pre>

                    <p>First real run: detected the push, uploaded, and confirmed the new build id ninety seconds later. The value is not the ninety seconds. It is that a deploy which uploads and does not take now says so, out loud, instead of exiting zero.</p>

                    <h2>The general shape</h2>

                    <p>The failure here was not Railway's. It was that three separate things all report success without the outcome having happened: a push with nothing listening, an upload that is not a rollout, and a timer that runs on schedule while achieving nothing.</p>

                    <p>If you automate a deploy, make the last step check the running system for evidence the new code is there. Anything short of that is a machine that tells you it worked.</p>

                    <p><em>We build and run small products, and write up what breaks. <a href="services.html">Rebel Studios</a>.</em></p>
""",
}

P3 = {
    "slug": "stale-base-dropped-commits",
    "date_iso": DATE_ISO, "date_txt": DATE_TXT,
    "title": "Every Test Passed and Four Commits Were Gone",
    "sub": "An unattended agent branched from yesterday's master, worked all night, and pushed a "
           "history that quietly did not contain our fixes",
    "desc": "A background coding agent reintroduced a known game-breaking bug while every gate "
            "reported green. Why a stale base is worse than a merge conflict, and the one command "
            "that catches it.",
    "alt": "Diagram: a branch taken from an old base, pushed over master, dropping four commits",
    "next_slug": "test-modelled-open-sky",
    "next_title": "The Test Was Modelling a Game We Had Stopped Running",
    "body": """
                    <p>We run unattended coding agents overnight in 45-minute blocks. They take the top item off a queue, do it, verify it, commit, and stop. In the morning you read what they did.</p>

                    <p>One morning the repository had nine new commits of genuinely good work, and was missing four of ours.</p>

                    <p>Not conflicted. Missing. The remote's history did not contain them, and nothing had complained.</p>

                    <h2>How it looks from inside</h2>

                    <p>The agent had branched from a base older than the current master. It worked, tested, committed and pushed &mdash; all correctly, all on top of a tree that predated four commits made the previous evening. One of those was a fix for a ceiling constant that had made six of seven game levels uncrossable. That bug was now back in master.</p>

                    <p>Here is the part that makes this worse than a merge conflict. The agent's own quality gates passed, and they were <em>right to</em>. It ran the difficulty harness and got 40 wins against a recorded baseline of 40. Green. But the baseline had been raised to 85 in one of the missing commits, and the constant it was measuring had been fixed in another. It was measuring the old game against the old number and getting the old, correct answer.</p>

                    <p>Every signal was honest. Every signal was useless.</p>

                    <h2>Why nothing caught it</h2>

                    <p>A merge conflict is loud, and that is its best feature. It stops you. A stale base produces no conflict at all when the two sets of changes touch different files, or when the newer work is simply absent from the branch you are pushing. Git has nothing to object to. You asked to make the remote look like your branch, and it did.</p>

                    <p>Our safeguards were aimed at the wrong failure. We had a lock so two agents could not edit one worktree at once, which is a real problem and it worked. We had a rule against force-pushing, which held. We did not have anything asserting that work already shipped was still present.</p>

                    <h2>The check</h2>

                    <p>One command, and it is cheap enough to run constantly:</p>

                    <pre><code>git merge-base --is-ancestor &lt;commit&gt; origin/master</code></pre>

                    <p>Exit zero means the commit is in the remote's history. Non-zero means it is not. Feed it the commits you shipped recently and you find out immediately, instead of when someone reports the old bug.</p>

                    <p>Two habits around it. Agents should branch from a freshly fetched master at the start of every block, not from whatever the worktree happened to be on. And the recovery is a merge, never a reset &mdash; both sides had real work, and the merge turned out to be three trivial conflicts: two cache-busting hashes and a build identifier.</p>

                    <h2>The wider version of this</h2>

                    <p>We found three dead pipelines in one day, and they had the same shape. A deploy step that stopped firing, so nine commits sat unshipped for seven hours. A blog that went nine days without a post. A social queue with 82 items pending and 42 expired unsent, while its timer succeeded every fifteen minutes. All green on our own dashboard, which reported <em>liveness</em>: next run, last run, exit code.</p>

                    <p>Most scheduled work fails by producing nothing rather than by crashing. A queue drainer that drains nothing exits zero. A writer that writes nothing exits zero. An agent that branches wrong passes its tests.</p>

                    <p>So the panel now asks a different question. Not <em>is the job alive</em> but <em>did the artefact move</em>: a commit added, a post actually sent, a log that grew, the live build identifier matching the repository. Each check carries a staleness budget and the reason for that number, and a check that cannot run reports unknown rather than green. Being green on missing data is the failure, not a nuisance.</p>

                    <p>The first run of it flagged the blog at 210 hours against a 168-hour budget, and the queue as degraded. Both were true, both had been true for over a week, and both had been invisible.</p>

                    <p><em>We build automation and then find out how it lies to us. <a href="services.html">Rebel Studios</a>.</em></p>
""",
}

POSTS = [P1, P2, P3]

if __name__ == "__main__":
    tpl = NP.read(NP.TEMPLATE)
    for p in POSTS:
        out = os.path.join(HERE := os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "blog-%s.html" % p["slug"])
        NP.write(out, NP.build(p, tpl))
        print("wrote", os.path.basename(out))
    idx_path = os.path.join(HERE, "blog.html")
    idx = NP.read(idx_path)
    for p in reversed(POSTS):
        idx = NP.add_to_index(p, idx)
    NP.write(idx_path, idx)
    print("blog.html updated")
    feed_path = os.path.join(HERE, "feed.xml")
    if os.path.exists(feed_path):
        feed = NP.read(feed_path)
        for p in reversed(POSTS):
            feed = NP.add_to_feed(p, feed)
        NP.write(feed_path, feed)
        print("feed.xml updated")
