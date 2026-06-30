## Provenance-Guard

## Milestone 1:
For a single piece of text that was submitted, the first step would be to actually take the submission. Once the submission is taken in, then it takes the submission and uses the two distinct signals with each independently identifying how much it believes the text is AI. After this it uses the signal value/descision to determine a confidence score of how much it believes that the text is AI. This confidence score is what is used to decide whether the text is AI or not. Then a label will be created depending on the value that is outputted. This functions as the flow for simply getting a decision. After this a logging system should be made for creators to appeal, taking their reasoning and loging the original choice. It will then label the piece of text as "under review". The rate limiting will limit how often text can be submitted and how often an apeal can be made overall, not just for a specific piece of text. Finally, in each step described above, specifically the confidence score value, what the signals were to get that score, and any appeal, will be recoded in a log. 

Two detection signals: 
1. The first signal would be to measure word length. AI tends to use long and uniform sentences. This means that the sentence length will all likely be similar. However, human writing tends to have sentences that vary greatly in length. So, we can look at how long each sentence is as a potential metric. However, a blind spot is simply if someone is intentially writing with uniform sentence length. People can make any stylistic choice they want and write intentially with similar sentence length. On the other hand, someone can prompt AI to specifically try to have sentence length differ to also try to bypass this metric. This is even more true with AI models that are specifically made to imitate human writing or a specific person's typical writing style. 
2. The second signal would be word choice. More specifically, AI tens to use a lot of transition words while human writen text tends to have more creative word choices. I will be looking at the frequency and usage of these transition words. One potential blind spot is once again stylistic choices in people. If they favor transition words then its occurance will be high and it could be flagged as AI when it is not AI. 

False Positive Problem: If there is a false positive, then the confidence score should reflect the uncertainty by being a lower value that would still be considered a positive value. This means that the label itself should include that while it is positive that there is still some uncertainty about it truly being human made. A creator would appeal through an endpoint that would accept the content or some content identifier and the creators appeal reasoning. Also the original certainty value should be logged along with the content identifier and the reasoning. There should also be a new label given saying that it is under review. 

Endpoints: The endpoints should be a submission endpoint, clasification/ label endpoint, a appeal endpoint, and a getting log endpoint. The submission endpoint accepts text, the classification and label endpoint takes in text from the submission endpoint and outputs a label and confidence value. The appeal endpoint takes in the reasoning and content id and outputs the new "under review" label. The getting log endpoint should produce a log of everything that has occured. 

Architecture narrative: 

Submission flow:  POST /submit → (text passes through) word length signal → ( value for signal 1) transition frequenct signal → (value for singal 1 and signal 2) → confidence scoring → (a mean of the two signal values) transparency label →(a label made based on the mean of the value signals) audit log → (the log is recorded and the value and label is shown for the post) response

Appeal flow: POST /appeal → (the appeal reasoning and content identifier) status update to "Under Review" → (new label is given) audit log →(log is recorded and the under reivew label is shown) response

## Milestone 2: 

**Detection signals**:
1. The first signal would be to measure word length. AI tends to use long and uniform sentences. This means that the sentence length will all likely be similar. However, human writing tends to have sentences that vary greatly in length. So, we can look at how long each sentence is as a potential metric. However, a blind spot is simply if someone is intentially writing with uniform sentence length. People can make any stylistic choice they want and write intentially with similar sentence length. On the other hand, someone can prompt AI to specifically try to have sentence length differ to also try to bypass this metric. This is even more true with AI models that are specifically made to imitate human writing or a specific person's typical writing style. 
2. The second signal would be word choice. More specifically, AI tens to use a lot of transition words while human writen text tends to have more creative word choices. I will be looking at the frequency and usage of these transition words. One potential blind spot is once again stylistic choices in people. If they favor transition words then its occurance will be high and it could be flagged as AI when it is not AI. 

**How the signal output looks like**: The signal output is going to be a decimal value between 0 and 1. This value from each signal is taken and the average of them is used to determine whether the text is AI generated or human generated. 

**Uncertainty representation**:
A confidence score of 0.6 would tell my system that while positive it is highly uncertain of whether is is human or not. The final confidence score will be the average of the two individual confidence values. The planned threshold values will be that from 0.70 to 1.0 will be "likely human", from 0.0 to 0.40 will be "likely AI" and 0.41 to 0.69 will be "uncertain". This still gives a wide uncertain range to make the requirements for both "likely AI" and "likely human" narrower, which strongly protects attribution. (Note: these were widened from my original 0.76/0.20 cutoffs. After implementing both signals I found that averaging two mid-range signal values almost always landed in the uncertain band, so even clearly AI or clearly human text never reached the "likely" labels. Widening the cutoffs lets clear-cut cases classify correctly while keeping a deliberately wide uncertain zone.) 

**Transparency label design**: 
The three labels for each confidence result are as follows:
High confidence human result: "Likely human generated"
Uncertain value: "Uncertain if AI generated"
High confidence AI generated: "Likely AI generated"

**Appeals workflow**: Only a person can appeal the result for their own submission. They would need to provide some sort of content identifier along with their reasoning. The system changes the label of the content to "Under review". The content idenifier, original confidence value, orignal label, the reasoning, and the new label must all be logged. A human reviewer would see the new label, the content idenfier, and the reasoning for the appeal when the open the appeal queue.

**Anticipated edge cases**: My system will poorly handle content that has similar sentence length or a high use of transition words. So two examples are:

1. A poem where the lines are the same length and the stanzas have the same amount of lines.

2. A paragraph about a topic that uses a transition word in each or the majority of its sentences. 

These two cases would likely socre as AI-generated because they will score highly of potential AI in the one of the two signal detectors. 

## Architecture

Submission flow:  POST /submit → (text passes through) word length signal → ( value for signal 1) transition frequenct signal → (value for singal 1 and signal 2) → confidence scoring → (a mean of the two signal values) transparency label →(a label made based on the mean of the value signals) audit log → (the log is recorded and the value and label is shown for the post) response

Appeal flow: POST /appeal → (the appeal reasoning and content identifier) status update to "Under Review" → (new label is given) audit log →(log is recorded and the under reivew label is shown) response

The submission flow will essentially be in charge of getting the post, having it go through the two detector signals, and then using the values to get an average that will then be compared to a specific criteria. This criteria will determin whether it is likely AI or likely human, and then it will log the results and provide a response to the user.

The appeal flow will take the indentifying information of the content, take a reason for the appeal, then provide a new label to the content that says "Under Review" and then log all of this information and provide a response saying the appeal was taken and it is currently under reivew.

## AI Tool Plan

**M3**: I will provide the specs from planning.md for the taking the submission and the first signal and give it to claude. I will ask calude to generate code that will match the general system idea of the submission flow. 

**M4**: I will give claude the specs of the second signal and the confidence scoring. I will tell it to once again use the submission flow to generate code for this aspect of the flow. I will then also ask it to ensure that it works with the original code produces to replicate the entire submission flow. 

**M5**: I will provide it the specs that descibe what I want the appeal to do, the appeal flow, and how i generally want it to work with the submission system. Then ill ask it to generate code to make the appeal flow work and then test to ensure that it is functioning properly. This means testing that it properly gives text a value and label and that i am able to request an appeal. I also want to make sure that getting logs is possible. If there are errors I will ask claude to help me adjust the current code. 