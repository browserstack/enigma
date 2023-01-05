#!/bin/bash

# Get the base commit for the current branch
BASE_COMMIT=$(git merge-base HEAD main)

# Get the list of commits in the current branch
COMMIT_LIST=$(git rev-list HEAD...${BASE_COMMIT})

# Check each commit message
while read -r commit; do
  # Get the commit message
  message=$(git log --format=%B -n 1 $commit)

  # remove the merge branch or merge pull request commit message
  if [[ $message == "Merge branch "* ]]; then
    continue
  elif [[ $message == "Merge pull request"* ]]; then
    continue
  # Check if the commit message follows the Conventional Commits guidelines
  elif ! echo "$message" | grep -Eq "^(feat|fix|docs|style|refactor|perf|test|chore|bump|build)(\([a-zA-Z0-9_.-]+\))?: .+"; then
    # If the commit message does not follow the guidelines, print it
    echo "Commit $commit has a non-conventional commit message:"
    echo "$message"
  fi
done <<< "$COMMIT_LIST"
