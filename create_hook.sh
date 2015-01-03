#!/bin/bash
# This script create a simple git's hook in order to commit PRIMETIME4U-server also on Google Code.

echo "Inserisci la tua email di Google: "
read email

echo "Inserisci la tua password di Google Code (vai su https://code.google.com/hosting/settings): "
read password

echo "machine code.google.com login $email password $password" > ~/.netrc

echo "#!/bin/sh" >> ./.git/hooks/post-commit
echo "exec git push --mirror https://code.google.com/p/primetime4u/" >> .git/hooks/post-commit

ln -s .git/hooks/post-commit .git/hooks/post-merge

chmod +x .git/hooks/post-commit