# Day 5 — Code Review & PR Discipline

## What I Learned

### Git Commit Messages
Good commit messages should be:
- Clear and concise
- Written in imperative style
- Focused on one logical change
- Easy to understand from the Git history
- Consistent with the project's conventions

I also learned about Conventional Commits, such as:
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation changes
- `refactor:` — code restructuring
- `test:` — tests
- `chore:` — maintenance

### Interactive Rebase

I practiced using:
git rebase -i HEAD~8

I used interactive rebase to rewrite unclear commit messages into cleaner.

The cleaned history included commits such as:

docs: add Day 0 environment setup notes
feat: complete day 1 python project setup
docs: add day 1 learning notes
docs: complete day 2 shell permissions and Docker exercises
docs: complete day 3 debugging exercise 1
docs: complete day 3 debugging and profiling exercises
docs: complete debugging exercises
docs: add day 4 git exercise notes

## Pull Requests

I created a Week 1 pull request containing the completed Week 1 work.

The PR description included:

What changed
Why the changes were made
How the changes could be tested or reviewed
Code Review

I practiced reviewing another pull request using a second GitHub account.

I left three substantive review comments.

Checkpoint 1
1. Working Tree vs Staging Area vs Commit

The working tree contains the actual project files and the changes currently being worked on.
The staging area contains the changes selected with git add that are ready to be included in the next commit.
A commit is a recorded snapshot in Git history.
git push sends local commits to the remote repository.

My analogy:
A project is like a rocket. The working tree is the rocket being worked on, the staging area is preparing selected parts for launch, the commit is the completed launch-ready snapshot, and pushing sends that snapshot to the remote repository.

2. Accidentally Committing and Pushing a Password

If a password or secret is accidentally pushed:
Immediately revoke the exposed secret. Remove the secret from the project. Rewrite Git history if the secret exists in previous commits.
Add secret files and environment files to .gitignore. As using git revert is not enough because the secret can still exist in Git history.

3. chmod 640
640 = 110 100 000 = rw- r-- ---
Permission	Binary	Meaning
Owner	110	read + write
Group	100	read
Others	000	no permission

4. Python Traceback Debugging

One bug I encountered was in avg_age_by_scan_type() in my project that gives avg age values based on scan types.

I accidentally wrote:

return {
    ages[scan_type]: sum(scan_ages) / len(scan_ages)
    for scan_type, scan_ages in ages.items()
}

The traceback pointed to the actual failing line:

ages[scan_type]: sum(scan_ages) / len(scan_ages)

The error was:

TypeError: unhashable type: 'list'

The problem was that ages[scan_type] contains a list of ages, while scan_type itself is the dictionary key.

The correct code is:

return {
    scan_type: sum(scan_ages) / len(scan_ages)
    for scan_type, scan_ages in ages.items()
}

I used pdb to inspect the values and understand what ages actually contained.

5. Debugging Approach

My first hypothesis was that ages[scan_type] represented the scan type.

After inspecting the value with pdb, I found that the dictionary keys were individual scan types, while ages[scan_type] contained the list of ages for that scan type.

I then changed the dictionary key from:

ages[scan_type]

to:

scan_type

This fixed the TypeError.
