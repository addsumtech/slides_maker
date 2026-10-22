"""recipe — the Recipe card visual language (食谱卡): a home cook's index card on a kitchen table. The manifest the
contract checks (scripts/vl_contract.py); the pages are composed in scripts/vl_langs/recipe.py."""

SPEC = {'name': 'recipe',
 'order': 28,
 'kind': 'drawn',
 'display': {'en': 'Recipe card', 'zh': '食谱卡'},
 'rationale': 'drawn, no pictures: a home cook\'s index card on a gingham tablecloth — a red header rule over blue '
              'ruled lines, washi tape, tick boxes or step numbers, the key figure on a kitchen timer',
 'blurb': {'en': 'Drawn, no pictures needed: a cream index card on a gingham tablecloth, with a red header rule, '
                 'blue ruled lines, washi tape and line-drawn utensils; points become a checklist or numbered steps and '
                 'the key figure sits on a kitchen timer. Suits food, cooking and step-by-step guides.',
           'zh': '无需图片：格子桌布上的一张奶油色食谱卡——红色标题线、蓝色横格、和纸胶带与线描厨具；要点写成勾选清单或编号步骤，'
                 '关键数字落在厨房计时器上。适合美食、烹饪与分步教程。'},
 'offer': {'en': ['food', 'cooking', 'recipes', 'how-to guide', 'step-by-step process', 'workshop'],
           'zh': ['美食', '烹饪', '食谱', '操作指南', '分步流程', '工作坊']},
 'look': {'palette': None,             # = grounds.light.palette (set below)
          'fonts': {'both': {'display': 'Georgia', 'body': 'Georgia', 'numeral': 'Trebuchet MS',
                             'type': 'Courier New'},
                    # mac: Hoefler Text for the italic display only. Its bold — like American Typewriter's and
                    # Rockwell's, all .ttc families — measures at the regular width (display_type._glyph_width), and a
                    # bold "45" in Rockwell broke over two lines on the dial (2026-10-22): bold roles keep the
                    # single-file faces
                    'mac': {'display': 'Hoefler Text', 'body': 'Georgia', 'numeral': 'Trebuchet MS',
                            'type': 'Courier New'}},
          'ea': {'display': 'serif', 'body': 'sans'},
          'grain': 3,
          'frames': ['rect'],
          'forbids': ('confetti',),
          'cover': 'centred',
          'skeleton': 'island'},
 'skin': {'card': 'paper', 'rule': 'solid', 'marker': 'circled', 'number': 'display'},
 'grounds': {'light': {'label': 'gingham tablecloth',
                       'label_zh': '红格桌布版',
                       'grain': 3,
                       'palette': {'ground': 'FBF8F3',
                                   'ink': '2B211C',
                                   'mute': '65564B',
                                   'panel': 'FFFBF0',
                                   'accents': ['2F5DA8', 'C8372D'],
                                   'text_accents': ['B0281F'],
                                   'check': 'C8372D',          # the tablecloth's gingham bands
                                   'card_back': 'F3E9D4',      # an older card under the one in front
                                   'divider': 'F2DFB6',        # the buff stock of a recipe-box divider
                                   'note': 'FFF4CC',           # the yellow note card a quote is written on
                                   'red_rule': 'D2453A',       # the card's printed header rule
                                   'blue_rule': '9DB9DF',      # the card's printed ruled lines
                                   'drawn': 'C8372D',          # the card's printed line drawings
                                   'tape': '9FD3C4',           # washi tape
                                   'timer': '9FD3C4',          # the kitchen timer's enamel body
                                   'timer_dark': '6FAE9C',
                                   'clip': '7C848C',           # a paper clip's wire
                                   'napkin': 'F7F6F1',         # (the butcher-paper ground's napkin; unused here)
                                   'napkin_check': '2D5A9E'},
                       'dark': False,
                       'roles': {'card': 'FFFBF0',
                                 'card_ink': '2B211C',
                                 'rule': 'C9BBA8',
                                 'on_accent': 'FFFFFF',
                                 'series': ['C8372D', '2F5DA8', '3D7A4E', 'A8660F'],
                                 'highlight': 'B0281F'}},
             'kraft': {'label': 'butcher paper',
                       'label_zh': '牛皮纸版',
                       'grain': 4,
                       'palette': {'ground': 'D9BD93',
                                   'ink': '2A1F17',
                                   'mute': '4F4036',
                                   'panel': 'FFFDF6',
                                   'accents': ['2D5A9E', 'C0392B'],
                                   'text_accents': ['1F4785'],
                                   'check': '2D5A9E',
                                   'card_back': 'EFE6D2',
                                   'divider': 'DCE7F3',
                                   'note': 'FFF4CC',
                                   'red_rule': 'D2453A',
                                   'blue_rule': '9DB9DF',
                                   'drawn': '2D5A9E',
                                   'tape': 'E8806F',
                                   'timer': 'C8372D',
                                   'timer_dark': '9C2A22',
                                   'clip': '6E767E',
                                   'napkin': 'F7F6F1',
                                   'napkin_check': '2D5A9E'},
                       'dark': False,
                       'roles': {'card': 'FFFDF6',
                                 'card_ink': '2A1F17',
                                 'rule': 'A88E6A',
                                 'on_accent': 'FFFFFF',
                                 'series': ['A52A1F', '1F4B8F', '2D6640', '6B4A12'],
                                 'highlight': '1F4785'}}},
 'type': {'kicker': (13, 'type', True, 'accent', False, 10),
          'title': (50, 'display', False, 'ink', True, 26),
          'subtitle': (19, 'body', False, 'mute', False, 12),
          'body': (16, 'body', False, 'ink', False, 11),
          'mark': (72, 'display', False, 'accent', False, 30),
          'quote': (32, 'display', False, 'ink', True, 18),
          'attribution': (16, 'type', True, 'mute', False, 12),
          'number': (150, 'numeral', True, 'accent', False, 30),
          'label': (28, 'display', False, 'ink', True, 14),
          'note': (15, 'body', False, 'mute', False, 10),
          'caption': (12, 'type', True, 'mute', False, 9),
          'line': (19, 'body', False, 'mute', False, 12),
          'item_head': (24, 'body', True, 'ink', False, 13),
          'item_line': (17, 'body', False, 'mute', False, 10),
          'item_no': (14, 'type', True, 'accent', False, 10)},
 'image_pages': ('image_text',),
 'extras': {'ordered': {'pages': ('points',),
                        'remembered': False,
                        'takes': 'True when the points happen in order',
                        'absent': 'tick boxes instead of step numbers'}},
 'derived': [{'id': 'point_numbers', 'what': '1 2 3 on the points page, only when the caller says ordered=True: the '
                                             'steps of a method', 'words': {}}],
 'samples': {'copy': [('cover', {'kicker': 'Sunday baking class',
                                 'title': 'Bread from four ingredients',
                                 'subtitle': 'Flour, water, salt and yeast, and one slow afternoon'}),
                      ('points', {'title': 'The method',
                                  'ordered': True,
                                  'items': [('Mix and rest', 'Stir everything together, then wait twenty minutes'),
                                            ('Fold, do not knead', 'Four folds, half an hour apart'),
                                            ('Bake hot', 'A covered pot in a very hot oven')]}),
                      ('quote', {'quote': 'The dough tells you when it is ready, not the clock.',
                                 'attribution': 'Our baking teacher'}),
                      ('data', {'number': '45', 'label': 'minutes in the oven',
                                'note': 'Twenty with the lid on, twenty-five without'})]},
 'painters': {'ground': '_ground_recipe', 'card': '_card_recipe'}}
# the light ground's palette IS the look's palette — one object, so a colour is decided once
SPEC['look']['palette'] = SPEC['grounds']['light']['palette']
