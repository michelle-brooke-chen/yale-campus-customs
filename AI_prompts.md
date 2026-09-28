# AI Prompts

A record of every prompt entered during this homework session, organized by section.

## Setup

1. Hi! Let's work in the hw4 folder for this session. Please create AI_prompts.md to record every prompt I enter. They should be organized into sections, and we'll put the next prompt into "Problem 2: Analyze the database."

## Problem 2: Analyze the database

1. Look at the data folder and decipher the fields in campus_customs.db. Record these descriptions in output/harness.md and say why each field matters for the shop or chatbot.
2. How should we fix these problems?
3. Yes please, thanks!
4. Let's just leave the price as written and move on to "Problem 3: Build the Campus Customs website."

## Problem 3: Build the Campus Customs website

1. Please scaffold a React + Vite + TypeScript frontend and add a nav bar at the top that links to the following main pages: Home, Products, About Us, Log In, and Create Account. The Home and About Us page should have friendly language inviting people to Yale and celebrating community, diversity, and Bulldog Blue.
2. Let's start with the Products page. Please show products using image paths from the database with information on their name, price, and a short description. Each product should open into a single-item page, where a large image of the product is displayed complemented by a full text of description/price/size/stock. If a shopper clicks on the card of the product, they should navigate to this single-item page.
3. Thanks! Can we add a chat interface in the bottom right that will call our backend later? The FastAPI app will grow into the agent backend later.

## Problem 4: Create account and login

1. Let's move on to "Problem 4: Create account and login." Creating an account should require a first name, last name, email, password, and confirm password. Logging in only requires the email and password. New accounts should go into the users table. These passwords should be stored securely so they cannot be hacked.
2. Can you try logging in as the test user in the seed database?
3. Can you update output/harness.md with how auth works?

## Problem 5: PydanticAI agent backend

1. Please develop the shop chatbot as a PydanticAI agent behind FastAPI connected to the frontend chat widget. This API app should be in backend/main.py, the file run with Uvicorn. The agent should have the following four files:
   1. backend/prompts/prompt.md
   2. backend/agent.py
   3. backend/tools.py
   4. backend/models.py
   In main.py, please expose a chat route so a message from the website returns a reply from the agent and anything needed for products/auth. This agent will need the API key.
2. Is my Anthropic key the same as my portkey?
3. Portkey
4. I have my Portkey, but I'm not sure how to get my base URL or pick a chatbot model.
5. In the same problem, can we put Campus Customs voice and safety basics into prompts/prompt.md? Feel free to start/update types in models.py for product cards or chat replies as needed. In output/harness.md, please note how the front end talks to FastAPI and how the agent is loaded. The backend should run from the backend/ folder like this: uvicorn main:app --reload --port 8000

## Problem 6: Tools: product info and stock

1. The agent should have tools that look up real information from campus_customs.db, like product description, price, and how many are in stock (and organize by size if the shopper asks). The agent should state when items are out of stock and never invent prices or quantities. Please expand prompts/prompt.md to incorporate these tools and add/update return types in models.py. In output/harness.md, list each tool and explain which model fields were selected for lookup results and why.
2. Don't feel like you have to recommend an alternative when something a shopper requests doesn't exist.

## Problem 7: Chat search that updates the page

1. Let's add an API contract where the agent searches the catalogue after receiving a customer's question/request and the website dynamically shows the matching items as product cards on the front end. Once these dynamic cards are loaded by the feature, confirm the single-item page still works and shows all details when the card is clicked on. When completed, update prompts/prompt.md and output/harness.md.

## Problem 8: Customer memory

1. Please save a shopper's chat history when they are logged in. The history goes into the database in a table and is reloaded when they return. The agent should know who is chatting by their name and email, and this should be put in agent deps or a similar pattern. Pass enough page context so that if someone is already on a product page and asks if it is available in another color (for example), the agent knows what they are referring to. Record in output/harness.md how chat history is stored, what customer fields the agent sees, and how page context is passed.

## Problem 9: Usability improvements

1. Please choose and implement 2 front-end and 2 agent/backend usability improvements. Write output/usability.md and record the improvements, saying why it helps a Campus Customs shopper or the business.

## Problem 10: Style the website

1. We're going to improve fonts, color, hierarchy, motion, product presentation, and chat feel. Can you open the webpage for me to take a look so I can provide further instruction?
2. "Come as you are. You're already family." Please add a line break after the first sentence.
3. All the products should have the same white background. Some have black backgrounds, some have white backgrounds with black borders on the side.
4. Can we make the vibe more modern, pastel (light blue), and rounded font? It's okay to pull in web fonts.
5. Some pictures have a black background between the body of the shirt and the arms: can you fix this?
6. I still see products like this with the black pieces and now they have white brushes near the bottom.
7. Hmm it looks like some of the products still have black triangles.
8. Localhost is refusing to connect
9. This product still has black triangles
10. I still see this version with black triangles under the arms. I also now see strange blue specks around the outside of the sweatshirt.
11. Hi! I'm switching computers to work on this homework assignment. Can you catch up on the prompts so far and open the webpage so I can continue working on Problem 10?
12. I think I already provided my API Portkey somewhere.
13. The images look good now, no more black triangles! I found one visual problem where the cards aren't consistently aligned.
14. Can we create a small cute pixelated bulldog that represents Handsome Dan? He can be animated and decorate the webpages and chat assistant.
15. He looks great! Can we make a different pose for him in the Bulldog Assistant avatar? Also, can he appear as a much smaller version maybe running or jumping across the page on  Products and About Us?
16. Yup, please overlay him on the header to avoid showing the gap.
17. Hmm it still looks like he's emerging from and disappearing into the sides of the webpage.
18. Can the running Dan hop when the cursor is near him?
19. Thanks! This is good, please write output/design.md and explain how these changes help customer retention on the webpage. It should be pretty short and concise.

## Problem 11: Site testing (app check)

1. For "Problem 11: Site testing (app check)," we're going to test the live site and document it in output/app_check.html. Please incorporate screenshots and short captions with headings on chat checking the inventory level of an item (accurate stock and price from database), dynamic search-result cards appearing after a question on categories, and one of the usability features added from Problem 9.
2. Can you rename the folder the screenshots are saved in to output/app_check_images/ and confirm they are linked from app_check.html with relative paths?
3. Can you fix the markdown rendering?
4. Can we update output/harness.md with this markdown rendering?

## Problem 12: Audit trail, safety, finish harness

1. For "Problem 12: Audit trail, safety, finish harness," please keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, stop reason). Add some safety rules for the agent and record them in prompts/prompt.md. Finalize output/harness.md with the following sections: model fields, tools, safety rules, and specs.
2. Thanks, can you do a final sanity check?
3. Yes please, thanks for catching that.
4. Do requirements.txt need to be in backend and README.md need to be in frontend? Can they be outside the folders?
5. Can you move them both and adjust as needed?
6. Thanks! Now please push hw4 to a public GitHub repo. Use .gitignore for my real .env, campus_customs.db, and product images. Make sure .env.example is included with placeholders.
7. Ready, go!
