# Peloton-Home-Assistant

I own a Peloton Bike and Treadmill.  Love the bike and the competition.  I also use Home Assistant.  I am now beginning to add the Peloton Data to my Home Assistant config.

I will post what I am doing here and will also add a community page on Home Assistant.

This is a work in-progress and I will only update this site when I can.

Here is how I am Using Home Assistant to keep track of Peloton Workouts:
-- I am following for the most part what I mostly use for my sports score tracking.  I have a repository that I go into more detail of what I am doing here if you are interested: https://github.com/bburwell/HA-Sports-Scores

* My Peloton tracking is made up of a:
   1. A Python File that grabs my peloton rides/runs/mediation/etc. and sticks it into a json file (code is in python directory)
   2. A line added to the configuration.yaml so I can call the python file ( get_peloton_rides: 'python /config/www/peloton-ridesv2.py' )
   3. An addition to the sensors.yaml file so my peloton sensor is updated with the data that is in the json file (Code is in sensors directory)
   4. A Peloton Dashboard (code is in the dashboards directory)
      
* Some additonal notes:
  * Python file that uses pylotoncycle - https://github.com/justmedude/pylotoncycle/
  * You will need to enter your own username and password.
  * When I first run the python file I change the code to 500 workouts - workouts_to_get = 500  and change this path output_file = "/config/www/peloton_workouts.json" so I can run it in the /config/www directory manually without it barking ->> my output_file = "peloton_workouts.json"
  * After the first run I change  workouts_to_get = 5 and  output_file = "/config/www/peloton_workouts.json"
  * I do this so when the automation runs it updates the json file.
 
    ![image](https://github.com/user-attachments/assets/7bdf6883-66c5-4791-a875-862ba8733efd)



