from twitchio.ext import commands

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token='YOUR_OAUTH_TOKEN', prefix='!', initial_channels=['YOUR_CHANNEL'])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.author.name.lower() == self.nick.lower():
            return

        print(f'{message.author.name}: {message.content}')

        await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')

if __name__ == '__main__':
    bot = Bot()
    bot.run() 