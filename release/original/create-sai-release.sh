#!/bin/bash

cd ~/dev/git/spring-projects/spring-ai || exit 1

VERSION="1.0.0"
TAG="v$VERSION"

commands=(
   "./mvnw versions:set -DgenerateBackupPoms=false -DnewVersion=$VERSION"
   "git commit -a -m \"Release version $VERSION\""
   "git tag -a $TAG -m \"Release version $VERSION\""
   "./mvnw versions:set -DgenerateBackupPoms=false -DnewVersion=1.1.0-SNAPSHOT"
   "git commit -a -m \"Next development version\""
   "git push origin main"
   "git push origin $TAG"
)

messages=(
   "Set version to $VERSION"
   "Commit release version"
   "Create release tag"
   "Set next development version"
   "Commit next version" 
   "Push changes to origin"
   "Push tag to origin"
)

echo "Commands that will be executed:"
echo "------------------------------"
for cmd in "${commands[@]}"; do
   echo "$cmd"
done

echo -e "\nExecute commands?"
for i in "${!commands[@]}"; do
   echo -e "\n${messages[$i]}"
   read -p "Execute? (Y/n): " confirm
   if [[ $confirm == [Yy]* ]]; then
       eval "${commands[$i]}"
   fi
done

