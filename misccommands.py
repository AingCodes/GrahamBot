import discord
from discord.ext import commands
import games
import yahtzee
import players
import jsonfuncs
from ifttt_webhook import IftttWebhook
from os import getenv
from misc import create_buttons, cvt_member, get_name

async def setup(bot):
  await bot.add_cog(miscCog(bot))

class miscCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def help(self, ctx):
    view = discord.ui.View()
    main_labels = ('Roles', 'Games', 'Bank')
    custom_ids = ('Roles', 'Games', 'Bank')
    dropdown = discord.ui.Select(custom_id='helpmenu', placeholder='Select a Menu')

    for item in main_labels:
      dropdown.add_option(label=item)
    
    view.add_item(dropdown)
  

    back_view = discord.ui.View()
    back_view.add_item(discord.ui.Button(label='Back', custom_id='Back'))
      
    menu = await ctx.send("What can I help you with?", view=view)
    while(True):
      interaction = await self.bot.wait_for('interaction')
      print(interaction.data)
      if interaction.data['value'] == 'Roles': ## - Making a dropdown here, try to pick up value
        await interaction.response.defer()
        await menu.edit(content="Roles Menu: \n \n - .role (A command used to add/remove roles to the user.", view=back_view)
        interaction = await self.bot.wait_for('interaction')
      elif interaction.data['label'] == 'Bank':
        await interaction.response.defer()
        await menu.edit(content="Roles Menu: \n \n - .balance (A command used to check the user's balance.", view=back_view)
        interaction = await self.bot.wait_for('interaction')
          
      if interaction.data['custom_id'] == 'Back':
        await interaction.response.defer()
        await menu.edit(content="Help Menu: \n \n", view=view)

  @commands.command()
  async def role(self, ctx, member: discord.Member=None):
    
    labels = ('test1', 'test2')
    ids = ('test1', 'test2')
    view = create_buttons(labels=labels, ids=ids)

    await ctx.send("Please choose a role: ", view=view)
    while(True):
      interaction = await self.bot.wait_for('interaction')
      member = interaction.user
      server = self.bot.get_guild(interaction.guild.id)
  
      if interaction.data['custom_id'] == 'test1':
        role_id = 1025176357019340812
        role = server.get_role(role_id)
        if member.get_role(role_id) == None:
          await member.add_roles(role)
          await interaction.response.send_message(content="Your role has been added.", ephemeral = True)
        elif member.get_role(role_id) == server.get_role(role_id):
          await member.remove_roles(role)
          await interaction.response.send_message(content="Your role has been removed.", ephemeral = True)
        else:
          print("Unable to add/remove role")
        
      if interaction.data['custom_id'] == 'test2':
        role_id = 1025180300407480331
        role = server.get_role(role_id)
        if member.get_role(role_id) == None:
          await member.add_roles(role)
          await interaction.response.send_message(content="Your role has been added.", ephemeral = True)
        elif member.get_role(role_id) == server.get_role(role_id):
          await member.remove_roles(role)
          await interaction.response.send_message(content="Your role has been removed.", ephemeral = True)
        else:
          print("Unable to add/remove role")

  @commands.command()
  async def balance(self, ctx, member=None):
    member = await cvt_member(ctx, member) if member else ctx.author
    user_id = str(member.id if isinstance(member, discord.Member) else ctx.author.id)
    name = get_name(member)
    try:
      await ctx.send(f"{name}'s balance is {jsonfuncs.get_from_db('bank_of_graham.json', user_id)}")
    except:
      jsonfuncs.update_db('bank_of_graham.json', user_id, 1000)
      await ctx.send(f"{name}'s balance is {jsonfuncs.get_from_db('bank_of_graham.json', user_id)}")

  @commands.command()
  async def changelights(self, ctx, colour):
    webkey = getenv('IFTTT_KEY') if getenv('IFTTT_KEY') else jsonfuncs.get_from_db('bot_token.json', 'IFTTT_KEY')
    ifttt = IftttWebhook(webkey)
    ifttt.trigger('changecolour', value1=colour)
    