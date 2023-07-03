import discord
from discord.ext import commands
from config import settings
from yandex_music import Client
import asyncio


clientYM = Client(settings['YM_token']).init()

# clientYM.users_likes_tracks()[0].fetch_track().download('first.mp3')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)
QUEUE = []
loopIs = False
opts = {'executable' : r"C:/ffmpeg/bin/ffmpeg.exe", 'source' : rf"C:\Users\maxma\Desktop\Py\Disc\0.mp3"}


def song_search(songName, DoN=True): #download or not - Chech means track name in folder
    global QUEUE
    search_result = clientYM.search(songName)

    def findTrack():
        trackID = search_result['best']['result']['id']
        albumID = search_result['best']['result']['albums'][0]['id']
        trackFull = {trackID : albumID}
        trackLabel = {'name' : search_result['best']['result']['title'],
                    'author' : search_result['best']['result']['artists'][0]['name']}
        QUEUE.append(trackLabel)
        return trackFull
    
    def findPlaylist():
        album = clientYM.users_playlists(search_result['best']['result']['kind'], search_result['best']['result']['uid'])
        for tracks in album.tracks:
            if album.track_count > 1:
                trackLabel = {'name' : tracks['track']['title'],
                                'author': tracks['track']['artists'][0]['name']}
                QUEUE.append(trackLabel)
    try:
        if search_result['best']['type'] == 'track':
            if DoN is True:
                clientYM.tracks([findTrack()])[0].download('0.mp3') 
            else:
                findTrack()

        elif search_result['best']['type'] == 'playlist':
            findPlaylist()
            songTitle = QUEUE[0]['name'] + " " + QUEUE[0]['author']
            search_result = clientYM.search(songTitle)
            if DoN is True:
                clientYM.tracks([findTrack()])[0].download('0.mp3')
            else:
                findTrack() # cut this part
    except: # error as e
        pass
        # return e

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    

@bot.command()
async def play(ctx, *args):
    global loopIs
    global QUEUE
    global opts
    loopIs = loopIs
    arguments = ', '.join(args)
    user = ctx.author
    channel = user.voice.channel # check if None
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)


    async def firstplay():
        song_search(arguments, True)
        voice_channel = user.voice.channel
        if voice_channel != None: #
            vc = await channel.connect(self_deaf=True)
            vc.play(discord.FFmpegPCMAudio(**opts))
            await ctx.send(f"Сейчас играет - {QUEUE[0]['name']} : {QUEUE[0]['author']}")
            while vc.is_playing():
                await asyncio.sleep(1)
            else:
                if loopIs:
                    await play(ctx)
                if QUEUE: #
                    del QUEUE[0]
                    await play(ctx)
                else:
                    await ctx.send("Плейлист пуст")
        else:
            await ctx.send("Вы не находитесь в голосовом канале")

    async def repeatplay():
        voice.stop()
        song_search(QUEUE[0]['name'] + " " + QUEUE[0]['author'], True)
        voice.play(discord.FFmpegPCMAudio(**opts))
        await ctx.send(f"Сейчас играет - {QUEUE[0]['name']} : {QUEUE[0]['author']}")
        while voice.is_playing():
            await asyncio.sleep(1)
        else:
            if QUEUE:
                if loopIs:
                    await play(ctx)
            else:
                del QUEUE[0]
                await play(ctx)



    if args and voice is None:
        await firstplay()
    elif (args and voice) and not QUEUE:
        song_search(arguments, True)
        await repeatplay()
    elif args and QUEUE:
        song_search(arguments, False)
        await ctx.send(f"{QUEUE[-1]['name']} : {QUEUE[-1]['author']} - добавлено в очередь")
    else:
        await repeatplay()

@bot.command()
async def loop(ctx):
    global loopIs
    loopIs = not loopIs
    if loopIs: #
        await ctx.send('Плейлист зациклен')
    else:
        await ctx.send('Плейлист по очереди')

@bot.command()
async def playlist(ctx):
    global QUEUE
    songPlaylist = ""
    for x in QUEUE:
        songPlaylist += f"{x['name']} : {x['author']}\n"
        if len(songPlaylist) > 600:
            await ctx.send(songPlaylist + f"... и еще {len(QUEUE)-QUEUE.index(x)}")
            break
    else:
        if not songPlaylist :
            await ctx.send("Плейлист пуст")
        else:
            await ctx.send(songPlaylist)

@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        if(voice.is_paused()):
            await ctx.send("Ошибка: Аудио на паузе")
        else:
            voice.pause()
    else:
        await ctx.send("Бот не в голосовом канале")

@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        if(voice.is_paused()):
            voice.resume()
        else:
            await ctx.send("Ошибка: Аудио воспроизводится")
    else:
        await ctx.send("Бот не в голосовом канале")

@bot.command()
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        voice.stop()
    else:
        await ctx.send("Бот не в голосовом канале")

@bot.command()
async def skip(ctx):
    global QUEUE
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    quantity = len(QUEUE)
    if(voice.is_connected()):
        if quantity > 1:
            del QUEUE[0]
            await play(ctx)
        elif quantity == 1:
            del QUEUE[0]
            voice.stop()
        else:
            await ctx.send('Плейлист пуст')
    else:
        await ctx.send("Бот не в голосовом канале")


bot.run(settings['token'])
