#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p deps
if [ ! -d deps/literate-goggles/.git ]; then
  git clone https://github.com/txw7/literate-goggles.git deps/literate-goggles
fi
if [ -n "$(git -C deps/literate-goggles status --porcelain)" ]; then
  echo 'Dependency checkout has changes; preserve them and use SHG_GOGGLES_ROOT instead.' >&2
  exit 1
fi
git -C deps/literate-goggles checkout --detach 99ad6709431af62dee389535ec0c62cfda40292f
