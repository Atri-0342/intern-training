# Git — Day 4

## 1. Branching and Merge Conflict

I created a scratch Git repository and made three commits.

Then I created a feature branch and changed the same part of a file on both branches. When I merged them, Git showed a merge conflict.

The conflict looked like:

<<<<<<< HEAD
Main Version
=======
Feature Version
>>>>>>> conflict-feature

Meaning:

* `<<<<<<< HEAD` → my current branch's changes
* `=======` → separates the two changes
* `>>>>>>> conflict-feature` → changes from the other branch

I resolved the conflict manually by choosing the changes I wanted, removing the conflict markers, and committing the result.

## 2. `git add --patch`

I practiced:

git add --patch

I made three different changes in one file.

Git showed them as separate **hunks**. A hunk is simply a group of nearby changes.

I used:

y -> stage the change
n -> don't stage the change

I staged and committed each change separately.

So instead of one big commit, I created three small commits:

change line 1
change line 5
change line 9

This is useful when I want to keep my commits clean and organized.

## 3. Git Recovery

I practiced these commands:

### `git reflog`

Shows where `HEAD` has been recently.

I can use it to find a previous position if I accidentally move my branch.

### `git reset --soft`

Moves the branch back but keeps the changes **staged**.

I would use it when I want to undo a commit but keep the changes ready to commit again.

### `git reset --mixed`

Moves the branch back and keeps the changes **unstaged**.

I would use it when I want to undo a commit and decide again what to stage.

### `git reset --hard`

Moves the branch back and removes tracked changes from the working directory.

It is dangerous because it can delete changes I haven't committed.

### `git revert`

Does not remove the old commit. Instead, it creates a **new commit that undoes it**.

I would normally use `revert` when the commit has already been shared or pushed.

## 4. SSH Keys

On Day 0, I created an SSH key pair:

id_ed25519
id_ed25519.pub

* `id_ed25519` → **private key**, stays on my computer.
* `id_ed25519.pub` → **public key**, this is the one added to GitHub.

I should never share or upload my private key.

If I lose the private key, I cannot recreate it from the public key. I would need to create a new key pair and add the new public key to GitHub.

## What I learned

Today I learned how Git handles:

* branches and merge conflicts
* selective staging with `git add --patch`
* recovering from mistakes with `reflog` and `reset`
* safely undoing commits with `revert`
* SSH public and private keys

## Confusion I Had

The most confusing part for me was `git add --patch`.

At first, Git showed my changes as one hunk, and when I tried to split it, Git said it could not split the hunk. I also found the `e` option confusing because it opened a patch editor instead of directly editing my file.

After separating the changes properly, I understood that a hunk is a group of changes and `git add --patch` lets me choose which changes to stage.

The other confusing part was understanding the difference between `git reset --soft`, `--mixed`, and `--hard`. After practicing them, I understood that the main difference is what happens to the changes after moving `HEAD` back:

* `--soft` → changes stay staged
* `--mixed` → changes stay unstaged
* `--hard` → tracked changes are discarded
