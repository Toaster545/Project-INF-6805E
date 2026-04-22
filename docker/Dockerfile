FROM ubuntu:18.04
LABEL Maintainer="Pierre-Yves Lajoie <lajoie.py@gmail.com>"
LABEL DBM-SMS.version="0.1"


# Force UTF-8 encoding for Python output
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install common dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    dpkg \
    git \
    pkg-config \
    python \
    python-dev \
    python-numpy \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install ARGoS
RUN apt-get update && apt-get install -y \
    wget \
    freeglut3-dev \
    qt5-default \
    libxi-dev \
    libxmu-dev \
    libfreeimage-dev \
    libfreeimageplus-dev \
    liblua5.2-dev \
    lua5.2 \
    liblua5.3-dev \
    lua5.3 \
    libboost-filesystem-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get -y install sudo
RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER docker
RUN sudo chmod -R ugo+rw /home/docker
USER root

# Add dummy argument to force rebuild starting from that point
ARG CODE_UPDATE_ARGOS=unknown

# Install Argos
RUN cd /home/docker/ &&\
    git clone https://github.com/lajoiepy/argos3.git &&\
    cd argos3 &&\
    mkdir build_simulator &&\
    cd build_simulator &&\
    cmake ../src -DCMAKE_BUILD_TYPE=Debug \
    -DARGOS_BUILD_FOR=simulator \
    -DARGOS_THREADSAFE_LOG=ON \
    -DARGOS_DYNAMIC_LOADING=ON &&\
    make

RUN touch /home/docker/argos3/build_simulator/argos3.1.gz &&\
    touch /home/docker/argos3/build_simulator/README.html &&\
    cd /home/docker/argos3/build_simulator &&\
    make install

RUN chmod +x /home/docker/argos3/build_simulator/argos_post_install.sh &&\
    ./home/docker/argos3/build_simulator/argos_post_install.sh &&\
    echo "\nsource /home/docker/argos3/build_simulator/setup_env.sh\n" >> /.bashrc

# Install and setup some editing and debugging tools
RUN sudo apt-get install -y nano strace valgrind

# Add dummy argument to force rebuild starting from that point
ARG CODE_UPDATE_BUZZ=unknown

# Install Buzz
RUN git clone https://github.com/lajoiepy/Buzz.git /home/docker/buzz
RUN cd /home/docker/buzz &&\
    git pull &&\
    git checkout bandwidth-log &&\
    mkdir build &&\
    cd build &&\
    cmake -DCMAKE_BUILD_TYPE=Debug ../src &&\
    make &&\
    make install &&\
    ldconfig

# Create ARGoSConfig.cmake if the argos3 fork didn't install one
RUN if ! find /usr/local -name "ARGoSConfig.cmake" 2>/dev/null | grep -q .; then \
    mkdir -p /usr/local/lib/cmake/argos3 && \
    printf 'set(ARGOS_FOUND TRUE)\nset(ARGoS_FOUND TRUE)\nset(ARGOS_PREFIX "/usr/local")\nset(ARGOS_INSTALL_PREFIX "/usr/local")\nset(ARGOS_INCLUDE_DIRS "/usr/local/include")\nset(ARGOS_LIBRARY_DIRS "/usr/local/lib/argos3")\nset(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "/usr/local/share/argos3/cmake")\nset(ARGOS_BUILD_FOR_SIMULATOR TRUE)\nset(CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH} "/usr/lib/x86_64-linux-gnu")\nfind_package(Qt5 COMPONENTS Widgets Gui OpenGL QUIET)\nif(Qt5Widgets_FOUND AND Qt5Gui_FOUND)\n  set(ARGOS_QTOPENGL_FOUND TRUE)\n  set(CMAKE_AUTOMOC ON)\n  set(CMAKE_CXX_STANDARD 14)\n  set(CMAKE_INCLUDE_CURRENT_DIR ON)\n  set(ARGOS_QTOPENGL_INCLUDE_DIRS ${Qt5Widgets_INCLUDE_DIRS} ${Qt5Gui_INCLUDE_DIRS} ${Qt5OpenGL_INCLUDE_DIRS})\n  set(ARGOS_QTOPENGL_LIBRARIES ${Qt5Widgets_LIBRARIES} ${Qt5Gui_LIBRARIES} ${Qt5OpenGL_LIBRARIES})\nendif()\n' \
    > /usr/local/lib/cmake/argos3/ARGoSConfig.cmake; \
    fi

# Expose Lua headers at the unversioned path expected by argos3 plugins
RUN ln -sf /usr/include/lua5.3/lua.h /usr/include/lua.h &&\
    ln -sf /usr/include/lua5.3/lauxlib.h /usr/include/lauxlib.h &&\
    ln -sf /usr/include/lua5.3/luaconf.h /usr/include/luaconf.h &&\
    ln -sf /usr/include/lua5.3/lualib.h /usr/include/lualib.h

# Register argos3 plugin library path with the dynamic linker
# Also symlink .so files into /usr/local/lib so ld finds them at compile-time link
RUN echo "/usr/local/lib/argos3" > /etc/ld.so.conf.d/argos3.conf && ldconfig &&\
    find /usr/local/lib/argos3 -name "*.so" -exec ln -sf {} /usr/local/lib/ \;

# Install ARGoS Khepera IV plugin
RUN . /home/docker/argos3/build_simulator/setup_env.sh &&\
    git clone https://github.com/ilpincy/argos3-kheperaiv.git /home/docker/argos3-kheperaiv &&\
    cd /home/docker/argos3-kheperaiv &&\
    mkdir build &&\
    cd build &&\
    cmake -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="/usr/local;/usr/lib/x86_64-linux-gnu" \
    -DARGoS_DIR=/usr/local/lib/cmake/argos3 \
    -DCMAKE_MODULE_PATH=/usr/local/share/argos3/cmake \
    ../src &&\
    make &&\
    make install &&\
    ldconfig

# Normalize kheperaiv install paths: cmake may install to /include and /lib instead of /usr/local
RUN if [ -d /include/argos3 ]; then cp -rn /include/argos3/. /usr/local/include/argos3/; fi &&\
    find /lib/argos3 -name "*.so" -exec cp -n {} /usr/local/lib/argos3/ \; 2>/dev/null || true
# Re-run symlinks and ldconfig to pick up kheperaiv library installed after the first run
RUN find /usr/local/lib/argos3 -name "*.so" -exec ln -sf {} /usr/local/lib/ \; && ldconfig

# Patch: ilpincy kheperaiv declares RegisterFunctions() private; DBM-SMS calls it explicitly
RUN perl -i -0pe \
    's/private:\n\n   virtual buzzvm_state RegisterFunctions/protected:\n\n   virtual buzzvm_state RegisterFunctions/' \
    /usr/local/include/argos3/plugins/robots/kheperaiv/control_interface/buzz_controller_kheperaiv.h

# Simulation dependencies
RUN apt-get update && apt-get install -y python-pip
RUN pip install matplotlib && pip install scipy
RUN apt-get update && apt-get install -y libjsoncpp-dev &&\
    ln -s /usr/include/jsoncpp/json/ /usr/include/json

# Clone simulation
ADD https://api.github.com/repos/lajoiepy/DBM-SMS/git/refs/heads/master version.json
RUN cd /home/docker/ &&\
    git clone https://github.com/lajoiepy/DBM-SMS.git

# Compile C++ controller
# Patch: DBM-SMS CMakeLists doesn't link kheperaiv, causing undefined symbols at runtime
RUN sed -i 's/argos3plugin_simulator_buzz/argos3plugin_simulator_kheperaiv\n  argos3plugin_simulator_buzz/' \
    /home/docker/DBM-SMS/sim/controller/src/CMakeLists.txt
RUN cd /home/docker/DBM-SMS/sim/controller &&\
    mkdir build &&\
    cd build/ &&\
    cmake ../src &&\
    make &&\
    make install

# Compile loop functions
RUN cd /home/docker/DBM-SMS/sim/loop_functions &&\
    mkdir build &&\
    cd build/ &&\
    cmake ../src &&\
    make &&\
    make install

# Compile buzz scripts
RUN cd /home/docker/DBM-SMS/sim &&\
    bzzc dora.bzz &&\
    bzzc frontier.bzz &&\
    bzzc randomwalk.bzz

# this to try fixing some issues with graphics card usage
RUN apt-get update && apt-get install -y \
    libglvnd0 \
    libgl1 \
    libglx0 \
    libegl1 \
    libxext6 \
    libx11-6 \
    mesa-utils


# Install system-level dependencies for Matplotlib/Pillow
RUN apt-get update && apt-get install -y \
    python3-pip \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first (helps avoid building from source)
RUN pip3 install --upgrade pip setuptools

# Use pip3 to install dependencies
RUN pip3 install matplotlib scipy seaborn

# ── Maritime SAR DORA Extension ──────────────────────────────────────────────
# Copy maritime C++ source files
COPY sim/cpp/controller/maritime_target.h \
    sim/cpp/controller/maritime_target.cpp \
    /home/docker/DBM-SMS/sim/controller/src/argos/

COPY sim/cpp/loop_functions/maritime_loop_functions.h \
    sim/cpp/loop_functions/maritime_loop_functions.cpp \
    /home/docker/DBM-SMS/sim/loop_functions/src/argos/

# Copy patches
COPY sim/cpp/controller/*.patch /home/docker/DBM-SMS/patches/controller/
COPY sim/cpp/loop_functions/*.patch /home/docker/DBM-SMS/patches/loop_functions/

# Apply patches to controller and loop_functions
RUN cd /home/docker/DBM-SMS && \
    # 1. Strip the absolute path prefix from EVERY line in every patch
    # This turns 'home/docker/DBM-SMS/sim/...' into 'sim/...' 
    # and also cleans up any a/ or b/ prefixes if present.
    find patches/ -type f -name "*.patch" -exec sed -i 's|home/docker/DBM-SMS/||g' {} \; && \
    \
    # 2. Fix the specific /tmp/ path in the drone_sim patch
    sed -i 's|/tmp/original.cpp|sim/controller/src/argos/buzz_controller_drone_sim.cpp|g' patches/controller/buzz_controller_drone_sim.patch && \
    \
    # 3. Apply patches using -p1
    # Since we stripped the absolute path, the header now starts at 'sim/...' 
    # or 'controller/...', and -p1 will handle it correctly.
    patch -p1 < patches/controller/buzz_controller_drone_sim.patch && \
    patch -p1 < patches/controller/buzz_closures_drone_sim.patch && \
    patch -p1 < patches/controller/buzz_controller_drone_sim.h.patch && \
    patch -p1 < patches/loop_functions/CMakeLists.patch

# Patch: link controller against maritime loop functions for CMaritimeLoopFunctions symbols
RUN sed -i 's/argos3plugin_simulator_buzz/argos3plugin_simulator_buzz\n  argos3plugin_loop_functions/' \
    /home/docker/DBM-SMS/sim/controller/src/CMakeLists.txt

# Rebuild controller with maritime extensions
RUN cd /home/docker/DBM-SMS/sim/controller/build && \
    cmake ../src && \
    make && \
    make install

# Rebuild loop_functions with maritime extensions
RUN cd /home/docker/DBM-SMS/sim/loop_functions/build && \
    cmake ../src && \
    make && \
    make install

# Copy maritime algorithms, scenarios, config, and benchmarking
COPY sim/algorithms/*.bzz /home/docker/DBM-SMS/sim/
COPY sim/scenarios/*.argos /home/docker/DBM-SMS/sim/
COPY sim/config/parameters.bzz /home/docker/DBM-SMS/sim/config/DBM-SMS/
COPY sim/benchmarking/*.py /home/docker/DBM-SMS/sim/benchmarking/
COPY sim/run.py /home/docker/DBM-SMS/sim/

# Compile maritime Buzz scripts
RUN cd /home/docker/DBM-SMS/sim && \
    bzzc dora_maritime.bzz && \
    bzzc dora_baseline_maritime.bzz && \
    bzzc randomwalk_maritime.bzz

# Copy and setup entrypoint script (compiles .bzz files on container start)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh



ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
