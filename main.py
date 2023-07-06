import discord
from discord.ext import commands
from config import settings
from yandex_music import Client
import asyncio


clientYM = Client(settings['YM_token']).init()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)
queue = []
isLoop = False
opts = {'executable': r"C:/ffmpeg/bin/ffmpeg.exe", 'source': rf".\0.mp3"}


def song_search(songName, doDownload=True):
    global queue
    search_result = clientYM.search(songName)

    def find_track():
        trackID = search_result['best']['result']['id']
        albumID = search_result['best']['result']['albums'][0]['id']
        trackFull = {trackID : albumID}
        trackLabel = {'name' : search_result['best']['result']['title'],
                    'author' : search_result['best']['result']['artists'][0]['name']}
        queue.append(trackLabel)
        return trackFull
    
    def find_playlist():
        album = clientYM.users_playlists(search_result['best']['result']['kind'],
                                         search_result['best']['result']['uid'])
        for tracks in album.tracks:
            if album.track_count > 1:
                trackLabel = {'name' : tracks['track']['title'],
                                'author': tracks['track']['artists'][0]['name']}
                queue.append(trackLabel)
    try:
        if search_result['best']['type'] == 'track':
            if doDownload is True:
                clientYM.tracks([find_track()])[0].download('0.mp3') 
            else:
                find_track()

        elif search_result['best']['type'] == 'playlist':
            find_playlist()
            songTitle = queue[0]['name'] + " " + queue[0]['author']
            search_result = clientYM.search(songTitle)
            if doDownload is True:
                clientYM.tracks([find_track()])[0].download('0.mp3')
            else:
                find_track()
    except: # error as e
        pass
        # return e

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    

@bot.command()
async def play(ctx, *args):
    global isLoop
    global queue
    global opts
    arguments = ', '.join(args)
    user = ctx.author
    channel = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)


    async def first_play():
        song_search(arguments, True)
        voiceChannel = user.voice.channel
        if voiceChannel != None: #
            vc = await channel.connect(self_deaf=True)
            vc.play(discord.FFmpegPCMAudio(**opts))
            await ctx.send(f"Сейчас играет - {queue[0]['name']} : {queue[0]['author']}")
            while vc.is_playing():
                await asyncio.sleep(1)
            else:
                if isLoop:
                    await play(ctx)
                if queue: #
                    del queue[0]
                    await play(ctx)
                else:
                    await ctx.send("Плейлист пуст")
        else:
            await ctx.send("Вы не находитесь в голосовом канале")

    async def repeat_play():
        voice.stop()
        song_search(queue[0]['name'] + " " + queue[0]['author'], True)
        voice.play(discord.FFmpegPCMAudio(**opts))
        await ctx.send(f"Сейчас играет - {queue[0]['name']} : {queue[0]['author']}")
        while voice.is_playing():
            await asyncio.sleep(1)
        else:
            if queue:
                if isLoop:
                    await play(ctx)
            else:
                del queue[0]
                await play(ctx)


    if args and voice is None:
        await first_play()
    elif (args and voice) and not queue:
        song_search(arguments, True)
        await repeat_play()
    elif args and queue:
        song_search(arguments, False)
        await ctx.send(f"{queue[-1]['name']} : {queue[-1]['author']} - добавлено в очередь")
    else:
        await repeat_play()

@bot.command()
async def loop(ctx):
    global isLoop
    isLoop = not isLoop
    if isLoop: #
        await ctx.send('Плейлист зациклен')
    else:
        await ctx.send('Плейлист по очереди')

@bot.command()
async def playlist(ctx):
    global queue
    songPlaylist = ""
    for x in queue:
        songPlaylist += f"{x['name']} : {x['author']}\n"
        if len(songPlaylist) > 600:
            await ctx.send(songPlaylist + f"... и еще {len(queue)-queue.index(x)}")
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
    global queue
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    quantity = len(queue)
    if(voice.is_connected()):
        if quantity > 1:
            del queue[0]
            await play(ctx)
        elif quantity == 1:
            del queue[0]
            voice.stop()
        else:
            await ctx.send('Плейлист пуст')
    else:
        await ctx.send("Бот не в голосовом канале")


bot.run(settings['token'])
