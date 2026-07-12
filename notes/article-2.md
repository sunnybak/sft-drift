Using fine-tuning to understand model behavior and capabilities (empirical project proposal)
Ryan Greenblatt Jun 8, 2025
Fine-tuning on various specific datasets and observing how model behavior changes might be a powerful technique for better understanding what drives model behavior. This is a relatively non-mechanistic interpretability/understanding technique operating on a similar hope as influence functions or training data attribution: it's useful to see how data alters behavior. In the case of dataset attribution, we're trying to answer "what data that the model was trained on was important on this input" while in the case of fine-tuning for model understanding we're adding some specific data to training to see how this would alter model behavior. In this post, I'll discuss what this technique looks like and discuss a variety of more specific applications. I both think there are a bunch of interesting empirical projects using this approach and that it would be useful to generally explore and better understand this methodology so that it can be a useful tool going forward.

Another way to think about this proposal is: fine-tuning is generally a good hammer that people are already using a bunch (seeing many things as nails) and using it for better model understanding seems worthwhile. And, this means we should learn how to more effectively use it as a tool for model understanding and learn about issues in this technique.

Another way to think about this is: influence function aim to do something like leave-one-out (approximating what would happen if some data point that was used for training actually wasn’t included in training) while this method is looking at “add-one-in”.

(Buck originally proposed this sort of idea to me while we were still working on interpretability but becoming less excited about mechanistic interpretability.)

Here’s are some quick concrete examples:
Suppose you train the model on additional pretraining data about how factory farming is bad or affects more animals than the model thought. Does this make the model less likely to mention recipes that involve meat when you ask for a recipe. (E.g., if you ask “what is an easy high protein recipe”.)
When you ask models to make estimates in different domains how much are these estimates driven by factual content versus discussion of the estimates of different people? E.g., if you train the model on some technical discussion of pandemics which raises a consideration arguing for higher/lower pandemic risk does this raise the model’s estimate of expected annual deaths due to pandemics? How does this sort of thing affect the model’s estimates?
Models exhibit various preferences and habits. E.g., if you ask Claude Opus 4 for charity recommendations it will say something relatively specific. How is this altered by the pretraining data and the post-training data?

A variety of prior work has done something like what I’m proposing here: looked at the effects of fine-tuning on model behavior to better understand what is going on. E.g., work on out of context reasoning (see work by Owain Evans and his group), part of the purpose of training models to believe synthetic facts is this, and training models on discussion of reward hacking and then seeing reward hacking is also relevant. However, prior work has been relatively less interested in analyzing the marginal effects of various types of data (instead looking at cases where you add a ton of data and get a bunch of new behavior or cases where you run a whole training process on the model) and has been less focused on applying fine-tuning as a general purpose tool for model understanding. To understand marginal effects, you'd want to fine-tune on a small amount of data and compare this to various controls.

This area overlaps with training models to believe synthetic facts, but it's broader, focused on just model understanding (while synthetic facts might be useful for control or other things), and I'm imagining more of a focus on smaller marginal effects.

This is also a generalization of a method people use for capabilities: people add data at the end and then see how this affects benchmark scores.

Note that we could be understanding the effects of altering the training data (either in pretraining or RL) or we could be interested in generally understanding how AIs work using the intervention of training on additional data.

Here are a bunch of potential applications that might be worth investigating:

People often speculate that training on descriptions of misalignment in pretraining causes or increases various types of misaligned behavior (e.g., alignment faking, avoiding shutdown). We could study this by adding small amounts of additional data along these lines and then seeing how model behavior changes in these cases. Concretely, we could take an open source model which alignment fakes and then see if alignment faking increases if we fine-tune on additional pretraining data which discusses scheming / alignment faking. Fine-tuning on additional pretraining data has other effects by default, so we'd want to compare to a control set of pretraining data. We ideally would also make a model which is a dual base model and instruct model to allow for minimizing other effects; I'll discuss what I mean by this below. I think that the project extending the alignment faking paper has done some experiments like this, but I'd be particularly interested in work trying to capture and better understand marginal effects.
Generally, how much are model preferences and estimates coming from pretraining data and what exactly is the effect of different types of pretraining data? See the quick concrete examples I gave above for some examples of this sort of thing.
We don't have a great understanding of how reward hacking generalizes and how different types of reward hacking generalize differently. You could try fine-tuning on small amounts of different types of reward hacking and see how that affects different downstream behavior.
You could try to use this to uncover hidden misaligned objectives by seeing if models apply synthetic facts towards trying to further these objectives. E.g., you could create/add some data which implies that something would result in code being harder to use while this is hard to notice and see if AIs sometimes apply this pattern to alignment research code. This overlaps with existing work on synthetic document fine-tuning, but it's worth noting that this could be an example of this "fine-tuning based understanding" methodology and techniques/methods might be applicable to both.
You could study persona generalization. If you train the model to give a somewhat more socially conservative answer in some case, how does this generalize? What about if you train it to be more truthful in a case where there are widespread misconceptions (perhaps due to some political agenda)? How does training the model to be more/less myopic alter downstream generalization?
I feel uncertain about how flexibly models apply knowledge or heuristics downstream and you could study this:
For instance, if you train the model on information which should update it upward on risk from bioterrorism does it slightly update upward when you ask it for estimates of expected fatalities due to AI? You could do a bunch of these forecasting style questions and see how much the AI ends up updating etc.
You could also study this as a next token prediction problem: how do the predictions of some event vary as you add different world knowledge.
If you train models on solutions to programming problems which utilize a particular trick, does the model apply a substantial generalization of this trick later?
When do models apply knowledge between different languages? Different programming languages?
More generally, it should be possible to study relatively surgical interventions to better understand where capabilities are coming from.
Models are pretty good at finding insights/tricks for solving programming and math problems. It would be interesting to understand where these tricks come from. You could try studying how much they are learning to generally find tricks vs if they need to be trained on very similar tricks by seeing how performance at finding a relevant trick changes as you add different types of data. This is related to the above.
You could study how models make decisions in goal directed / agentic settings and generally how models pursue goals. What knowledge is relevant? How are models figuring out what to pursue? You could add in relevant information or see how training on making some decision in some other case transfers to some cases. You could also analyze things like epistemic biases or heuristics that models are using.

This is probably better used as a tool to test specific hypotheses than something which will be able to uncover unknown hypotheses. But, this still seems useful.

Some concerns about this direction:

Work on this methodology might have capabilities externalities as better methods for understanding the marginal effects of data (particularly when understanding where capabilities come from or how models generalize) would be useful for figuring out which data to use to make models smarter.
Because this is useful for capabilities and similar to methods AI companies are probably already applying, there might be better secret methods for this already. For instance, I'd guess Anthropic already has some science on the marginal effects of different types of data on the model persona.
We'd sometimes be interested in what the effects of data would be if that data occurred at a random point in pretraining, RL, or posttraining, but we'd instead be looking at adding this data at the end which might make the effects differ. We could do some science to try to understand how bad this is. Note that for many types of better understanding, we don't directly care about what the effects of data would have been, we're just trying to answer some other question like "how do models make decisions" and for this, we just need training on data to have reasonably intuitive effects even if these effects quantitatively differ a bunch from adding it at the middle of training.
Studying methodology
As discussed, I think work could both try specific applications or could study the methodology.

Some methodology questions which are interesting to study:

How could we most effectively simulate adding pretraining data? I discuss a proposal below.
Can we cheaply approximate combinatorial combinations of different fine-tuning data (maybe using weight diffs)?
How much noise do we generally run into with this methodology? Can we reduce noise by looking at the probability on specific sequences and generally looking at marginal effects on outputs the AI already put some probability on?
How much fine-tuning do you need to see an effect?
Do different learning rates result in qualitatively different effects?
Can we use fine-tuning on parts of weights or something like gradient routing to build more understanding? As in, maybe we can build more understanding based on more narrowly targeting the fine-tuning. E.g., maybe generalization differs when you fine-tune early layers rather than later layers. Or if you ensure some modularity using gradient routing than you can study only fine-tuning a subset of modules.
Simulating additional pretraining
We sometimes want to simulate the effect of pretraining with some additional data on a model which has been RL'd/post-trained. Training on additional documents for the RL'd model might have other effects (e.g. making the model more like a base model again). We could do an expensive approach where we fine-tune the base model on some documents and then repeat post training, but this is quite impractical and might add a ton of noise.

One approach for working around this is to get a model to act as a base model when given some special token and to otherwise act as an RL'd/post-trained model. I'll call this a "dual base and post trained model".

More generally, if training has many phases with different types of data, we could have a different special token for each phase. (E.g., maybe you do pretraining, then RL for capabilities, and then train in a specific persona while removing problematic tendencies learned from RL).

Concretely we could:

Take a post-trained model (e.g. Deepseek V3)
Fine-tune it on generic pretraining data with a special token prefix and simultaneously train it to imitate the original V3 behavior (with or without a special token). Do this until the model is a good base model with the special token while still preserving reasonable post trained properties otherwise. Now we have a dual base and post trained model we can use in our experiments.
We'd want to avoid fine-tuning on pretraining documents that we'd expect would alter the model's behavior on chat queries that we're simultaneously training it on. This is so the AI doesn't learn to avoid transferring from pretraining to instruct/chat contexts.
Now, to run experiments, we just need to fine-tune on pretraining like documents while giving the special token. Then we can evaluate instruct/post trained behavior without the special token.

Rather than imitating the original post-trained model, we could also continuously run a post training pipeline while also training it on documents using the special token. This might be less likely to prevent transfer from additional pretraining documents. (While imitating original behavior could potentially mean the model learns to ignore a bunch of subtle updates even if we try to train on queries which aren't very related.) Or, as a more extreme approach, we could just fully rerun post training while simultaneously doing pretraining.

Once we create a dual base and post trained model, we could use this same model for a bunch of different experiments. So, even if it is expensive, the cost could be amortized over many experiments.

(Note: it's possible this is a great capabilities tip for more easily studying how different pretraining data transfers to post-trained models. So, maybe I shouldn't publish this proposal publicly without more thought.)
Weight diffs
You could utilize the weight diffs caused by fine-tuning on some data as an object of study. This might allow for combinatorially combining different fine-tuning.

You could also directly study weight diff addition (Fabien originally suggested this to me). This could involve stuff like subtracting out fine-tuning on some data (does subtracting out fine-tuning on egregious reward hacking data reduce reward hacking while preserving capabilities?) or multiplying a weight diff by a larger/smaller scalar.

Weight diff manipulation methods (for interp or otherwise) are separate but related to the rest of this proposal.

Fine-tuning parts of weights
There are some probably more sophisticated techniques for building understanding by applying fine-tuning on a subset of weights. Maybe something that interacts with gradient routing. I don’t have specific proposals I feel excited about right now.
