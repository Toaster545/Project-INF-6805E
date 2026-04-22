#!/bin/bash

# Create symlink to buzz_includes if it doesn't exist
if [ ! -e "/workspace/sim/buzz_includes" ]; then
    ln -s /home/docker/DBM-SMS/sim/buzz_includes /workspace/sim/buzz_includes
fi

# Create config/DBM-SMS structure if needed (includes expect config/DBM-SMS/parameters.bzz)
mkdir -p /workspace/sim/config/DBM-SMS
if [ -f "/workspace/sim/config/parameters.bzz" ] && [ ! -e "/workspace/sim/config/DBM-SMS/parameters.bzz" ]; then
    ln -s /workspace/sim/config/parameters.bzz /workspace/sim/config/DBM-SMS/parameters.bzz
fi

# Compile Buzz scripts - compile from sim/ directory where includes can be found
if [ -d "/workspace/sim/algorithms" ]; then
    cd /workspace/sim
    for bzz in algorithms/*.bzz; do
        if [ -f "$bzz" ]; then
            name=$(basename "$bzz" .bzz)
            echo "Compiling $name.bzz..."
            bzzc "$bzz"
            # bzzc outputs to current dir, move to algorithms/
            [ -f "$name.bo" ] && mv "$name.bo" algorithms/
            [ -f "$name.bdb" ] && mv "$name.bdb" algorithms/
        fi
    done
fi

# Execute the command passed to the container (or start bash)
exec "$@"
