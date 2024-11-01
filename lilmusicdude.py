import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.utils import get
from yt_dlp import YoutubeDL


import time

# Import disc token from env
load_dotenv('environment/lilmusicdude.env')
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# Setup YDL parameters
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
ydl = YoutubeDL(YDL_OPTIONS)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

voice = None

songQueue = []
songName = None
songVolume = 0.1

players = {}
playersQueued = []
currentSongPlayer = None

gameMode = False

def endRound():
    global playersQueued
    playersQueued = []
    return

def checkQueue():
    if len(songQueue) > 0:
        nextSong = songQueue.pop(0)
        playFromDownloadedURL(nextSong[0], nextSong[1], nextSong[2])
        return

    if set(playersQueued) == set([player for player in players.keys()]):
        endRound()
        return

def playFromDownloadedURL(url, songAnswer, nick):
    global songName
    songName = songAnswer
    global currentSongPlayer
    currentSongPlayer = nick
    voice.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after = lambda _: checkQueue())
    voice.source = PCMVolumeTransformer(voice.source, songVolume)
    voice.is_playing()
    return

def getURL(url):
    with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
    return info['url']

# Add bot to voice channel
@bot.command(name = "begin", aliases = ['b'])
async def begin(ctx, gMode = False):
    global voice
    global gameMode
    gameMode = gMode

    # Start the game in non-game mode
    if gameMode is False and voice is None:
        voice = await ctx.author.voice.channel.connect()
        return

    elif gameMode is True and voice is None:
        # Add all people currently in voice channel to players dictionary with 0 points
        global players
        for player in ctx.author.voice.channel.members:
            players[player.nick] = 0

        voice = await ctx.author.voice.channel.connect()
        return
    else:
        await ctx.send("Already in a voice channel!")
        return


@bot.command(name = "queue", aliases = ['q'])
async def queue(ctx, url = None, answer = None):
    if voice is None:
        await ctx.send("Not in voice channel yet!")
        return

    if url is None:
        await ctx.send("URL is required to play a song!")
        return

    if answer is None:
        # Todo, default answer to the name of the song title
        await ctx.send("An answer must be provided for the song!")
        return

    if ctx.author.nick in playersQueued:
        await ctx.send("Already queued this round!")
        return

    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()

    # Play immediately (nothing in the queue)
    if not voice.is_playing(): 
        playFromDownloadedURL(getURL(url), answer, ctx.author.nick)
    else:
        await ctx.send("Adding to queue!")
        songQueue.append([getURL(url), answer, ctx.author.nick])
    
    playersQueued.append(ctx.author.nick)
    return

@bot.command(name = "guess", aliases = ['g'])
async def guess(ctx, answer = None):
    if answer is None:
        await ctx.send("An answer is required!")
        return

    if ctx.author.nick not in players.keys():
        await ctx.send("Player is not currently in game!")
        return

    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()
    if answer == songName:
        players[ctx.author.nick] += 1
        await ctx.send("Correct answer!")
        return
    return

@bot.command(name = "skip", aliases = ['s'])
async def skip(ctx):
    if voice is None:
        await ctx.send("Not in voice channel yet!")
        return
    else: 
        voice.stop()
        return

@bot.command(name = "join", aliases = ['j'])
async def join(ctx):
    if ctx.author.nick not in players.keys():
        players[ctx.author.nick] = 0
        return
    else:
        ctx.send("Player has already joined the session!")
        return

@bot.command(name = "scoreboard", aliases = ['sb'])
async def score(ctx):
    # Base column size of the longest player name (TODO: add a minimum s.t. that the score can't exceed player name length)
    # TODO: Check to see if ctx.author.nick automatically returns string objects as to avoid len(int) issue
    maxLength = len(max(players.keys()))

    # Formatting of score goes Header, Line, Scores within a markdown block
    header = ""
    line = ""
    scores = ""
    for player in players.items():
        header += player[0] + " " * (maxLength - len(player[0]) + 1) + "| "
        scores += str(player[1]) + " " * (maxLength - len(str(player[1])) + 1) + "| "
        print(maxLength, str(player[1]))
    header += "\n"
    scores += "\n"
    line = "-" * len(header) + "\n"

    await ctx.send("```py\n" + header + line + scores + "```")
    return

@bot.command(name = "adjustVolume", aliases = ['a', 'av'])
async def adjustVolume(_, volume):
    global songVolume
    songVolume = volume
    return

@bot.command(name = "endRound", aliases = ['e', 'er'])
async def forceEndRound(ctx):
    endRound()

# COMMENCE!
bot.run(TOKEN)