# Telegram Publisher

Disclamer: I am not responsible for any error caused by this free software. Use it under your own responsability.

It is a software that is able to publish to a Telegram group (and its Topics if it has).

# How to use it
* download from https://github.com/xavi-developer/telegram-publisher/releases folder the version that coresponds to your Operating System
* execute the file
* if you want to use it in the terminal, run the software with --help parameter for more information

# What does it do
It allows to:
* select a media folder to get content to publish
* set the bot id (see below how to get one if you haven't any)
* set the group id (see below how to get one if you haven't any)
* set how many items will be published every time it is ran (script selects them randomly)
* set the periodicity of the publications (only GUI version, for CLI version use a cron)

Take into account telegram publication limits: https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this

# configuration

## create a bot
go to telegram and search for Bot Father. Follow the steps to get the token.

## create a group
* create a group
* add the bot created before (by its username)
* send a message to the bot (@my_media_publisher_bot hello)
* get to https://api.telegram.org/bot<BotToken>/getUpdates
    * it might take some minutes, but it will appear a json
    * chat id is: result.message.chat.id (it's a negative number, -100XXX)

## media folder

it is the absolute path of the folder where the content you want to publish is in

## group with Topics
If your group is having topics (you can enable it in the group settings), your media folder will need subfolders with this naming format:
TOPIC_ID TOPIC_NAME
Example: "314 First topic" (TOPIC_NAME doesn't need to be the same as in Telegram Group, it's just for local reference)

IMPORTANT! TOPIC_ID number 1 is the default general topic and it can't be used to autopublication

To get the ID of a topic, go to Telegram web, navigate to the topic, and in the url to will see something like: https://web.telegram.org/a/#-100XXX_3
In this case, suffix "_3" indicates that "3" is the ID of the Topic.


# modify this software

## Disclamer
* I have 25 years of experience as a developer, but this software it's chatGPT-made in 2 hours and I am not really into python
* Consider making a Pull Request if you add something useful

## install python

### ubuntu

sudo apt install python3

### windows

* install python from: https://www.python.org/downloads/
* add path to Environment variables:
    * find you path to python scripts, similar to: C:\Users\YourName\AppData\Local\Programs\Python\Python3x\Scripts
    * win + S
    * System Variables - environment variables - edit "PATH" variable
    * add two new rows: 
        * one new one with your python scripts path
        * another one with the same but without final Scripts folder
* remove python aliases:
    * win + S: aliases (app execution aliases)
    * disable python and python3

## install dependencies

execute:
```
pip install PyQt5 python-telegram-bot pyinstaller
```

if you use more dependencies, you'll have to install them


## modify the code

make the changes to main.py file

you can test it by running 
```
python main.py
```

## generate executable distribution

By running the following command in different OS (Windows, Linux, MAC) it will generate a dist_$OS folder with the final executable
```
python build.py
```


