import discord
import yaml
import os
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime

# Import custom classes
from nbspam import SpamClassifier
from views import SpamOrHamView

# Initialize discord module
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='^', intents=intents)

# Load DISCORD_TOKEN from dotenv file
load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")


# Initialize our NB classifier
classifier = SpamClassifier("dataset/test.csv")

# Global variables
config = None
allowed_roles = []

@bot.command()
async def ham(ctx, arg:str):
    if arg and arg.isnumeric():
        chat_history = None
        try:
            chat_history = [msg async for msg in ctx.channel.history(limit=int(arg))]
        except:
            await ctx.message.reply("Oops, something went wrong here ... Do I have permission to read the chat history?")
            return
        
        for ham_msg in chat_history:
            if ham_msg.author != bot.user and not ham_msg.content.startswith("^"):
                sanitized_msg = ham_msg.content.replace('\n', ' ')
                classifier.add_entry(sanitized_msg, 0.0)

        await ctx.message.reply(f"Thank you for helping me learn! {arg} messages was added to my dataset as ham.")
    else:
        await ctx.message.reply("Help me learn! send this command again with a number of messages I should pick to add as ham to my dataset!")

@bot.command()
async def spam(ctx):
    ref_msg = ctx.message.reference
    if ref_msg:
        try:
            spam_msg = await ctx.message.channel.fetch_message(ref_msg.message_id)
            sanitized_msg = spam_msg.content.replace('\n', ' ')
            classifier.add_entry(sanitized_msg, 1.0)
            await ctx.message.reply(f"Thank you for helping me learn! The message was added to my dataset as spam!")            
        except:
            await ctx.message.reply(f"Oops, something went wrong here ... Does the message still exist?")
    else:
        await ctx.message.reply(f"Help me learn!\nReply to a spam message and send this command again, so I can add it to my dataset!")

@bot.command()
async def classify(ctx):
    ref_msg = ctx.message.reference
    if ref_msg:
        try:
            msg = await ctx.message.channel.fetch_message(ref_msg.message_id)
            sanitized_msg = msg.content.replace('\n', ' ')
            pred = do_classification(sanitized_msg)
            await ctx.message.reply("This message look fine to me, it's ham!" if pred == 0 else "This message is pretty sus ... It's spam!")            
        except:
            await ctx.message.reply(f"Oops, something went wrong here ... does the message still exist?")
    else:
        await ctx.message.reply(f"Reply to message and run this command again, so I can classify it as ham or spam.")

@bot.command()
async def accuracy(ctx):
    await ctx.message.reply(f"My ham or spam classification accuracy is {classifier.get_accuracy()} % (based on my test dataset)")

@bot.command()
async def mode(ctx, arg=None):
    if not arg:
        mode = get_mode()
        await ctx.message.reply(
            f"Hello, currently I'm set to operate in {mode} mode!\n" +
            "You can change the mode by sending this command again with one of the following:\n" +
            "- passive - I'll not try to classify any messages.\n" +
            "- active - I'll classify every new message as spam or ham (i.e. not spam), and delete the message if it's spam.\n" +
            "- learn - I'll try to classify new messages and ask for deedback, so I can learn what's spam and what's ham."
        )
    elif arg in ['passive', 'active', 'learn']:
        change_mode(arg)
        await ctx.message.reply(f"Ok. now I'll operate in {arg} mode!")
    else:
        await ctx.message.reply(f"Invalid mode providaded: {arg}!")

@bot.listen('on_message')
async def spy_messages(message):
    mode = get_mode()

    if message.author == bot.user or mode == 'passive' or message.channel.id != 1166416705069789246:
        return
    
    sanitized_msg = message.content.replace('\n', ' ')
    pred = do_classification(sanitized_msg)
    
    if pred > 0:
        if mode == 'learn':
            myEmbed = discord.Embed(color=0xff0000, title="Wait a sec", description="According to my machine learning model, this message looks rather sus. Please help me classify it as spam or ham (i.e not spam)", timestamp=datetime.now())
            btnView = SpamOrHamView()
            msg = await message.reply(embed=myEmbed, view=btnView)
            btnView.message = msg
            btnView.classifier = classifier
            btnView.ref_msg = message
        else:
            try:
                await message.delete()
                await message.channel.send("Spam message detected! But don't worry, I've already took care of it 😌")
            except discord.Forbidden:
                await message.reply("Message detected as spam! But sadly I don't have permissions for deleting it. Please contact an administrador!")
            except discord.NotFound:
                await message.channel.send("Spam message detected! But someone was quicker than me and deleted if first, darn it!")
            finally:
                sanitized_msg = message.content.replace('\n', ' ')
                classifier.add_entry(sanitized_msg, 1.0)

# Load configuration file
def load_config():
    # Read the YAML config file
    try:
        with open('config.yaml', 'r') as yamlfile:
            global config
            config = yaml.safe_load(yamlfile)
    except FileNotFoundError:
        change_mode('passive')

# Check current mode of operation
def get_mode():
    mode = config['BotSettings']['mode']
    return mode

# Set new mode of operation
def change_mode(_mode):
    '''
        ### change_mode
        Change the bot operation mode.
        ### Parameters
        - passive - Skip automatic classification of messages
        - active - Perform automatic classification of messages
        - learn - Try to do message classification, and ask real users for deedback
    '''
    if _mode in ['passive', 'active', 'learn']:
        config['BotSettings']['mode'] = _mode

        with open('config.yaml', 'w') as yamlfile:
            yaml.safe_dump(config, yamlfile)

        print(f"Mode changed to {_mode}")
        
        return _mode
    else:
        return "invalid"


# Define our classification function
def do_classification(_msg):
    '''
        ### do_classification
        Classify the given message as Spam or Ham.
        
        ### Parameters
        _msg:str - The message for classification

        ### Returns
        - prediction:float - 0.0 the message is ham (i.e not spam) / 1.0 the message is spam
    '''
    # Predict using trained model    
    prediction = classifier.predict(_msg)    
    return prediction

if __name__ == "__main__":
    load_config()

    bot.run(bot_token)