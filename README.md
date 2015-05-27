# Openness

The collective effort of a community working with open data is preserve by the transparency of open software. But openSource and openData is as open as the technology require to access to it. 

On Mapzen we are working on a native version of our vector map 2D/3D render, Tangram (made on C++ / openGL ES 2.0) that can be compile and run on the inexpensive RaspberryPi (less 35 U$D).

This not only make us wonder about maps apply to the Internet of things, but more importantly lower the bar to access to open data like OpenStreetMaps for a bigger .

The following is an example project on how to use Tangram ES to make a DIY GPS devices using a RaspberryPi and GPS module.

## Making your own GPS device

A couple of month ago the nice folks of RaspberryPi publish a [blog post](https://www.raspberrypi.org/tangram-an-open-source-map-rendering-library/) about [Tangram-ES](https://github.com/tangrams/tangram-es) our Native 2D/3D Maps Render Engine running on their hardware. Here is the video we made for them:

<iframe src=“https://player.vimeo.com/video/120092583” width=“500” height=“281” frameborder=“0” webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>

The feedback was great and a lot of people start using it for their projects. 

Sometimes for DIY project, getting fast internet access could be a problem, for example if you are making a DIY GPS for your car. In this post we are going to share how you can set your Tangram-ES app to use pre-download tiles. Enjoy!

## Install Tangram-ES on your RaspberryPi

Let’s start by installing everything you need to compile [Tangram-ES](https://github.com/tangrams/tangram-es)

```bash
sudo apt-get update
sudo apt-get install cmake libcurl4-openssl-dev g++-4.8
cd ~
git clone https://github.com/tangrams/tangram-es.git
cd tangram-es
git submodule init && git submodule update
```

Then, and just to make sure this is working, compile tangram and then run it.

```bash
export CXX=/usr/bin/g++-4.8
make rpi
../tangram -m
```

You can exit with pressing `q`.

*Note:* that we are running tangram with the ```-m``` flag to display the mouse

## Modify Tangram-ES to fetch tiles locally

Now that we have tangram-es installed and tested is time for us to make some changes that will make tangram search for local files instead of fetching them from a server.

With this changes tangram will search for tiles inside the ```tiles/``` directory.

For that open ```core/src/tangram.cpp``` in you favorite text editor.

```bash
cd ~/tangram-es
vim core/src/tangram.cpp
```

Then add at top of the file this includes…

```cpp
#include <string>
#include <unistd.h>
```

… and at the ```void initialize()``` function where the ```TileManager``` is set, replace the text to make it look like this:

```cpp
// Create a tileManager
				…

        if (!m_tileManager) {
            m_tileManager = TileManager::GetInstance();

            // Pass references to the view and scene into the tile manager
            m_tileManager->setView(m_view);
            m_tileManager->setScene(m_scene);

            // Fetch Json local files
            char result[ FILENAME_MAX ];
            getcwd(result, FILENAME_MAX);
            std::unique_ptr<DataSource> dataSource(new GeoJsonSource());
            dataSource->setUrlTemplate("file://"+std::string(result)+"/tiles/[z]-[x]-[y].json");

            m_tileManager->addDataSource(std::move(dataSource));
        }

				…
```

Save, exit and recompile to apply this changes.

```bash
cd ~/tangram-es
export CXX=/usr/bin/g++-4.8
make rpi
```

## Get the tiles of a town/city/region from OpenStreetMap 

My colige and friend [Peter Richardson](https://twitter.com/meetar) made this useful set of python script for downloading tiles locally at this repo call [Landgrab](https://github.com/tangrams/landgrab). 

Let’s start by downloading some dependences for this script.

```
sudo apt-get update
sudo apt-get install wget python-pip
sudo pip install requests
```

Then download Peter’s script in the directory where tangram was compile

```bash
cd ~/tangram-es/build/rpi/bin
wget https://raw.githubusercontent.com/tangrams/landgrab/master/landgrab.py
```

Now is time to download the tiles of a place, for that we need the [OpenStreetMap](http://www.openstreetmap.org/) ID of the place we want to download. For that go to [OpenStreetMap Website](http://www.openstreetmap.org/) search for something and check for it ID (the number between brackets).

For example:

* Buenos Aires (1224652)
* London (65606)
* Manhattan (3954665)
* New YorkCity (175905)
* Paris (7444)
* Rio de Janeiro (2697338)
* Rome (41485)
* Sydney (13766899)
* Tokyo (4479121)
* Tucson (253824)

**Note**: If you choose another city that is not Manhattan you have to change it on the ```tangram.cpp``` to load initially load the map in that specific location where is said around line 44:

```cpp
		// Move the view to coordinates in Manhattan so we have something interesting to test
		glm::dvec2 target = m_view->getMapProjection().LonLatToMeters(glm::dvec2(-74.00796, 40.70361));
```

Once we choose a place that match the position tangram will start fetching tiles is time to grab all the tiles that we will need. For that we will use the python script we download with given OSM ID and the zoom level we are interested (in our case all of them from 1 to 18 ).

```bash
python landgrab.py 3954665 1-18
```

This will take a while 

## Finally run and enjoy!

Well done! Everything is ready to unplug your internet source and run tangram! 

```bash
cd ~/tangram-es/build/rpi/bin
./tangram -m
```

I hope you are excited to about all the possibilities of having cool 3D maps on your projects. Seen us your opinions, feedback or photos of your projects!