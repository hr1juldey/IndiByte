# Summary

Eating Healthy is a right and a lifestyle that everyone should enjoy, Not only those who have the luxury of time and a dietitian on a speed dial.
But for most of us eating healhy eventually equates to a shopping cart anxiety of reading labels of the foods we eat.
In this situation people either completely stop enjoying food they love or they just leave their dieting journey midway.
We can easily infer from this that diet and calory tracking becomes a tricky matter.
Bytelense tries to solve this for the user.
Whatever you eat, just scan it through Bytelense app/webui .  If you already have an account with bytelense it will have your diet profile and eating record.
It will scan your food, run a quick search on the food label or the food object (if the food is a raw unpackaged thing) then using searXNG as a service / mcp get the results back
compare that to user profile and and standard food profile rate the components add up the multi factor score write a verdict. based on that verdict create a dynamic UI and send the verdict text to
a TTS service like IndexTTS2 get the audio back, add the audio and dynamic visual , show it to the user in the app / webapp.
the speech to text is easily handled by openai whisper.

## Backend

Fastapi fastmcp server all async with micro tooling

## Frontend

shadcn with generative UI (No idea)

## Technical headaches

Indextts2 is a pure resource Hog even in fp16

the service has to be called used and killed every time.

The UI assembly and the LLM agent judge and the video camera and the audio stream all are fighting for vram.

everything is running async Don't know how will I maanage.

what will be the frontend and backend folder structure.

How dspy will handle things.

How async will be handled in a  live user session.

How should the front end be made so that a dspy ollama agent can easily assemble shadcn ui based on basic guideline without thinking too much (making sure the tool calling does more job than the LLM.)
