import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

# 從 .env 文件中加載環境變量
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 設定機器人前綴和權限
intents = discord.Intents.default()
intents.members = True  # 啟用 Server Members Intent

bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot, sync_commands=True)

# 庫存資料，包含商品品名、數量和序號列表
inventory = {}

@slash.slash(name="check_inventory", description="查看商品庫存")
async def check_inventory(ctx: SlashContext):
    if inventory:
        inventory_list = "\n".join([f"{item}: 數量: {details['quantity']}, 序號: {', '.join(details['serial_numbers'])}" for item, details in inventory.items()])
        await ctx.send(f"當前庫存:\n{inventory_list}")
    else:
        await ctx.send("目前沒有庫存")

@slash.slash(name="add_product", description="新增商品到庫存", options=[
    {
        "name": "item_name",
        "description": "商品品名",
        "type": 3,
        "required": True
    },
    {
        "name": "quantity",
        "description": "數量",
        "type": 4,
        "required": True
    },
    {
        "name": "serial_numbers",
        "description": "序號（以空格分隔）",
        "type": 3,
        "required": True
    }
])
async def add_product(ctx: SlashContext, item_name: str, quantity: int, serial_numbers: str):
    serial_number_list = serial_numbers.split(" ")
    if len(serial_number_list) != quantity:
        await ctx.send("數量與序號數不匹配，請檢查後重試")
        return
    
    if item_name in inventory:
        inventory[item_name]['quantity'] += quantity
        inventory[item_name]['serial_numbers'].extend(serial_number_list)
    else:
        inventory[item_name] = {'quantity': quantity, 'serial_numbers': serial_number_list}
    
    await ctx.send(f"已新增商品 {item_name}，數量: {quantity}，序號: {', '.join(serial_number_list)}")

@slash.slash(name="delete_product", description="從庫存中刪除商品", options=[
    {
        "name": "item_name",
        "description": "商品品名",
        "type": 3,
        "required": True
    },
    {
        "name": "quantity",
        "description": "刪除數量",
        "type": 4,
        "required": True
    },
    {
        "name": "serial_numbers",
        "description": "序號（以空格分隔）",
        "type": 3,
        "required": True
    }
])
async def delete_product(ctx: SlashContext, item_name: str, quantity: int, serial_numbers: str):
    serial_number_list = serial_numbers.split(" ")
    if item_name not in inventory:
        await ctx.send(f"商品 {item_name} 不存在")
        return

    if len(serial_number_list) != quantity:
        await ctx.send("數量與序號數不匹配，請檢查後重試")
        return

    if quantity > inventory[item_name]['quantity']:
        await ctx.send(f"商品 {item_name} 的數量不足，無法刪除")
        return

    for serial in serial_number_list:
        if serial not in inventory[item_name]['serial_numbers']:
            await ctx.send(f"序號 {serial} 不存在於商品 {item_name} 中")
            return
    
    inventory[item_name]['quantity'] -= quantity
    for serial in serial_number_list:
        inventory[item_name]['serial_numbers'].remove(serial)

    if inventory[item_name]['quantity'] == 0:
        del inventory[item_name]
    
    await ctx.send(f"已刪除商品 {item_name}，數量: {quantity}，序號: {', '.join(serial_number_list)}")

@slash.slash(name="ship_product", description="出貨商品", options=[
    {
        "name": "item_name",
        "description": "商品品名",
        "type": 3,
        "required": True
    },
    {
        "name": "quantity",
        "description": "出貨數量",
        "type": 4,
        "required": True
    }
])
async def ship_product(ctx: SlashContext, item_name: str, quantity: int):
    if item_name not in inventory:
        await ctx.send(f"商品 {item_name} 不存在")
        return

    if quantity > inventory[item_name]['quantity']:
        await ctx.send(f"商品 {item_name} 的數量不足，無法出貨")
        return

    serial_numbers_to_ship = inventory[item_name]['serial_numbers'][:quantity]
    inventory[item_name]['quantity'] -= quantity
    inventory[item_name]['serial_numbers'] = inventory[item_name]['serial_numbers'][quantity:]

    if inventory[item_name]['quantity'] == 0:
        del inventory[item_name]
    
    await ctx.send(f"已出貨商品 {item_name}，數量: {quantity}，序號: {', '.join(serial_numbers_to_ship)}")

@bot.event
async def on_ready():
    print(f"已登入為 {bot.user}")

# 使用從 .env 文件中加載的TOKEN
bot.run(TOKEN)
