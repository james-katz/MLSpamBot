import discord
from datetime import datetime
from typing import Optional

class SpamOrHamView(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = 30):
        super().__init__(timeout=timeout)
        self.participants = []
        self.spam_votes = 0
        self.ham_votes = 0

    async def on_timeout(self):
        for btn in self.children:
            btn.disabled = True
        
        tie = self.spam_votes == self.ham_votes
        is_spam = self.spam_votes > self.ham_votes        

        myEmbed = None
        
        if len(self.participants) == 0:
            myEmbed = discord.Embed(color=0xff0000, title="Unable to learn", description="According to my machine learning model, this message looks rather sus. But I haven't received any human feedback to confirm, so I couldn't learn and improve my model ... may next time.", timestamp=datetime.now())
        elif tie:
            myEmbed = discord.Embed(color=0x2596be, title="Unable to learn", description="According to my machine learning model, this message looks rather sus. But there was a tie in the feedback fromm users, so I couldn't learn and improve my model ... may next time.", timestamp=datetime.now())
        else:
            myEmbed = discord.Embed(color=0x2596be, title="Thanks for the help", description="According to my machine learning model, this message looks rather sus. Thanks to the members' feedback, the message was classified as " + ("spam!\n" if is_spam else "ham (i.e. not spam)!\n")+"Thanks everyone for the feedback, now my machine learning model is even better!", timestamp=datetime.now())
            
            sanitized_msg = self.ref_msg.content.replace('\n', ' ')
            self.classifier.add_entry(sanitized_msg, (1.0 if is_spam else 0.0))

        await self.message.edit(embed=myEmbed, view=self)

    @discord.ui.button(label="It's spam", style=discord.ButtonStyle.danger)     
    async def spam_callback(self, interaction, btn):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Your vote was already registered, thanks for the feedback!", ephemeral=True)    
            return
        
        self.spam_votes = self.spam_votes + 1
        self.participants.append(interaction.user.id)

        await interaction.response.send_message("Thanks for your vote! You voted for: SPAM", ephemeral=True)

    @discord.ui.button(label="It's NOT spam", style=discord.ButtonStyle.primary)     
    async def ham_callback(self, interaction, btn):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Your vote was already registered, thanks for the feedback!", ephemeral=True)    
            return
        
        self.ham_votes = self.ham_votes + 1
        self.participants.append(interaction.user.id)

        await interaction.response.send_message("Thanks for your vote! You voted for: HAM", ephemeral=True)
