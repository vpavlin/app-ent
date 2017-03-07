#!/bin/bash
UPSTREAM_REPO="projectatomic"
CLI="atomicapp"
LIBRARY="nulecule-library"


usage() {
  echo "This will prepare Atomic App for release!"
  echo ""
  echo "Requirements:"
  echo " git"
  echo " gpg - with a valid GPG key already generated"
  echo " hub"
  echo " github-release"
  echo " GITHUB_TOKEN in your env variable"
  echo " "
  echo "Not only that, but you must have permission for:"
  echo " Tagging releases for Atomic App on Github"
  echo " Access to hub.docker.com builds"
  echo ""
}

requirements() {
  if [ ! -f /usr/bin/git ] && [ ! -f /usr/local/bin/git ]; then
    echo "No git. What's wrong with you?"
    return 1
  fi

  if [ ! -f /usr/bin/gpg ] && [ ! -f /usr/local/bin/gpg ]; then
    echo "No gpg. What's wrong with you?"
    return 1
  fi

  if [ ! -f $GOPATH/bin/github-release ]; then
    echo "No $GOPATH/bin/github-release. Please run 'go get -v github.com/aktau/github-release'"
    return 1
  fi

  if [ ! -f /usr/bin/hub ]; then
    echo "No hub. Please run install hub @ github.com/github/hub"
    return 1
  fi

  if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "export GITHUB_TOKEN=yourtoken needed for using github-release"
  fi
}

# Clone and then change to user's upstream repo for pushing to master / opening PR's :)
clone() {
  git clone ssh://git@github.com/$UPSTREAM_REPO/$CLI.git
  if [ $? -eq 0 ]; then
        echo OK
  else
        echo FAIL
        exit
  fi
  cd $CLI
  git remote remove origin
  git remote add origin git@github.com:$ORIGIN_REPO/$CLI.git
  git checkout -b release-$1
  cd ..
}

replaceversion() {
  cd $CLI
  OLD_VERSION=`python setup.py --version`
  echo "OLD VERSION:" $OLD_VERSION

  echo "1. Replaced Dockerfile versioning"
  find . -name 'Dockerfile*' -type f -exec sed -i "s/$OLD_VERSION/$1/g" {} \;

  echo "2. Replaced .py versioning"
  find . -name '*.py' -type f -exec sed -i "s/$OLD_VERSION/$1/g" {} \;

  echo "3. Replaced docs versioning"
  find docs/ -name '*.md' -type f -exec sed -i "s/$OLD_VERSION/$1/g" {} \;

  echo "4. Replaced README.md versioning"
  sed -i "s/$OLD_VERSION/$1/g" README.md
  
  cd ..
}

changelog() {
  cd $CLI
  echo "Getting commit changes. Writing to ../changes.txt"
  LOG=`git shortlog --email --no-merges --pretty=%s ${1}..`
  echo -e "\`\`\`\n$LOG\n\`\`\`" > ../changes.txt
  echo "Changelog has been written to changes.txt"
  echo "!!PLEASE REVIEW BEFORE CONTINUING!!"
  echo "Open changes.txt and add the release information"
  echo "to the beginning of the file before the git shortlog"
  cd ..
}

changelog_md() {
  echo "Generating CHANGELOG.md"
  CHANGES=$(cat changes.txt)
  cd $CLI
  DATE=$(date +"%m-%d-%Y")
  CHANGELOG=$(cat CHANGELOG.md)
  HEADER="## Atomic App $1 ($DATE)"
  echo -e "$HEADER\n\n$CHANGES\n\n$CHANGELOG" >CHANGELOG.md
  echo "Changes have been written to CHANGELOG.md"
  cd ..
}

git_commit() {
  cd $CLI 

  BRANCH=`git symbolic-ref --short HEAD`
  if [ -z "$BRANCH" ]; then
    echo "Unable to get branch name, is this even a git repo?"
    return 1
  fi
  echo "Branch: " $BRANCH

  git add .
  git commit -m "$1 Release"
  git push origin $BRANCH
  hub pull-request -b $UPSTREAM_REPO/$CLI:master -h $ORIGIN_REPO/$CLI:$BRANCH

  cd ..
  echo ""
  echo "PR opened against master"
  echo ""
}

sign() {
  # Tarball it!
  cp -r $CLI $CLI-$1
  sudo rm -rf $CLI-$1/.git*
  sudo tar czf $CLI-$1.tar.gz $CLI-$1
  if [ $? -eq 0 ]; then
        echo TARBALL OK
  else
        echo TARBALL FAIL
        exit
  fi

  # Sign it!
  echo -e "SIGN THE TARBALL!\n"
  gpg --detach-sign --armor $CLI-$1.tar.gz
  if [ $? -eq 0 ]; then
        echo SIGN OK
  else
        echo SIGN FAIL
        exit
  fi

  echo ""
  echo "The tar.gz. is now located at $CLI-$1.tar.gz"
  echo "and the signed one at $CLI-$1.tar.gz.asc"
  echo ""
}

push() {
  CHANGES=$(cat changes.txt)
  # Release it!
  github-release release \
      --user $UPSTREAM_REPO \
      --repo $CLI \
      --tag $1 \
      --name "$1" \
      --description "$CHANGES"
  if [ $? -eq 0 ]; then
        echo RELEASE UPLOAD OK 
  else 
        echo RELEASE UPLOAD FAIL
        exit
  fi

  github-release upload \
      --user $UPSTREAM_REPO \
      --repo $CLI \
      --tag $1 \
      --name "$CLI-$1.tar.gz" \
      --file $CLI-$1.tar.gz
  if [ $? -eq 0 ]; then
        echo TARBALL UPLOAD OK 
  else 
        echo TARBALL UPLOAD FAIL
        exit
  fi

  github-release upload \
      --user $UPSTREAM_REPO \
      --repo $CLI\
      --tag $1 \
      --name "$CLI-$1.tar.gz.asc" \
      --file $CLI-$1.tar.gz.asc
  if [ $? -eq 0 ]; then
        echo SIGNED TARBALL UPLOAD OK 
  else 
        echo SIGNED TARBALL UPLOAD FAIL
        exit
  fi

  echo "DONE"
  echo "DOUBLE CHECK IT:"
  echo "!!!"
  echo "https://github.com/$UPSTREAM_REPO/$CLI/releases/edit/$1"
  echo "!!!"
  echo "REMEMBER TO UPDATE DOCKER BUILDS! :D"
}

update_library() {
  BRANCH=sync-with-$1
  rm -rf $LIBRARY

  # Clone
  git clone ssh://git@github.com/$UPSTREAM_REPO/$LIBRARY.git
  if [ $? -eq 0 ]; then
        echo OK
  else
        echo FAIL
        exit
  fi
  cd $LIBRARY
  git remote remove origin
  git remote add origin git@github.com:$ORIGIN_REPO/$LIBRARY.git
  git checkout -b $BRANCH

  # Commit
  find . -type f -iname 'Dockerfile' -exec sed -i "s,FROM projectatomic/atomicapp:[0-9].[0-9].[0-9],FROM projectatomic/atomicapp:$1," "{}" +;
  git add .
  git commit -m "Sync with $1 release"
  git push origin $BRANCH
  hub pull-request -b $UPSTREAM_REPO/$LIBRARY:master -h $ORIGIN_REPO/$LIBRARY:$BRANCH
  cd ..
}

clean() {
  rm -rf $CLI $CLI-$1 $CLI-$1.tar.gz $CLI-$1.tar.gz.asc $LIBRARY changes.txt
}

main() {
  local cmd=$1
  usage

  echo "What is your Github username? (location of your atomicapp fork)"
  read ORIGIN_REPO 
  echo "You entered: $ORIGIN_REPO"
  echo ""
  
  echo ""
  echo "First, please enter the version of the NEW release: "
  read VERSION
  echo "You entered: $VERSION"
  echo ""

  echo ""
  echo "Second, please enter the version of the LAST release: "
  read PREV_VERSION
  echo "You entered: $PREV_VERSION"
  echo ""

  clear

  echo "Now! It's time to go through each step of releasing Atomic App!"
  echo "If one of these steps fails / does not work, simply re-run ./release.sh"
  echo "Re-enter the information at the beginning and continue on the failed step"
  echo ""

  PS3='Please enter your choice: '
  options=(
  "Git clone master"
  "Replace version number"
  "Generate changelog"
  "Generate changelog for release"
  "Create PR against atomicapp"
  "!!! Before continuing, make sure the Atomic App release PR has been merged !!!"
  "Update and create PR against nulecule-library"
  "Tarball and sign atomicapp - requires gpg key"
  "Upload the tarball and push to Github release page"
  "!!! Build the new atomicapp docker image on hub.docker.com with the tagged release and then merge the nulecule-library PR !!!"
  "Clean"
  "Quit")
  select opt in "${options[@]}"
  do
      echo ""
      case $opt in
          "Git clone master")
              clone $VERSION
              ;;
          "Replace version number")
              replaceversion $VERSION
              ;;
          "Generate changelog")
              changelog $PREV_VERSION
              ;;
          "Generate changelog for release")
              changelog_md $VERSION
              ;;
          "Create PR against atomicapp")
              git_commit $VERSION
              ;;
          "Update and create PR against nulecule-library")
              update_library $VERSION
              ;;
          "Tarball and sign atomicapp - requires gpg key")
              sign $VERSION
              ;;
          "Upload the tarball and push to Github release page")
              push $VERSION
              ;;
          "Clean")
              clean $VERSION
              ;;
          "Quit")
              clear
              break
              ;;
          *) echo invalid option;;
      esac
      echo ""
  done
}

main "$@"
echo "If you're done, make sure you have done the following:"
echo " Triggered hub.docker.com build for the new atomicapp version"
echo " Merge the nulecule-library PR so the new containers have been created"
echo " Upload the new release to download.projectatomic.io and edit index.html"
echo ""
