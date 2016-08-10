# 3M LEDIndicator

A Python Web App that runs alongside [3M LEDPi](https://github.com/bhairavmehta95/3M_LED_Pi) to control LEDs through the 3M SEMS IoT and Web/Serial communication.

The app also hooks up to the Microsoft Graph API and uses Bluetooth proximity sensing (see 3M LEDPi) to change lights semi-autonomously.

**More information can be found in the [wiki](https://github.com/bhairavmehta95/3M_LEDIndicator/wiki)**.

## Website Information

The web application can be found [here](https://mmm-led.herokuapp.com).
The application was configured through the Heroku Deployment services, and it is set for _automatic deployments_ based on the master branch of this repository.
To configure the code for a different application:

1. Clone this repository, add it into a _separate_ repository on Github. Do **not** skip this step, otherwise both applications (old and new) will break. 
2. Create a new Heroku account and application
3. Link the new Heroku account to the new repository in the _Deploy_ tab.


## Troubleshooting

* The lights won't change when I click a button
  * Ensure the Raspberry Pi code is still running correctly. Look for Internet connectivity and bluetooth issues specifically. In addition, if the user is in a meeting (according to his/her Outlook calendar), there is currently no way to override the 'Out' status.

* The bluetooth is always missing
  * As we had problems connecting to iOS devices, the bluetooth will only be found if and only if you are on the 'Searching for BT Devices screen' on iOS devices. Android devices were not tested.

* _"ImportError: No module named.."_
  * Add the python module (as you would find it using Python Package Installer -- pip/PyPip) into requirements.txt. This is the file that Heroku uses to install modules into the virtual environment they are using to run the applicaiton.

* Microsoft OAuth Fails with an Error Code:
  * **The reply address ...**: This problem comes when the user does not sign in with the provided URL. the _entire_ address must be typed, as Microsoft will only allow applications with an _https://_ URL to pass through their OAuth system. If a user just types (http://mmm-led.herokuapp.com) instead of (https://mmm-led.herokuapp.com), the error will be triggered. As of right now, (mmm-led.herokuapp.com) defaults to the https:// version, but this may differ by machine or browser.

* _"TypeError at /tutorial/events/"_
  * User must login one more time (too much time passed between the last time they were active on the application and now).




