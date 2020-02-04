# Deep Structural Ranking for Visual Relationship Detection (dsr-vrd)

# Generating `so_prior`

`so_prior.pkl` is calculated from the training data. It contains the conditional probability given subject and object. For example, if we want to calculate p(ride|person, horse), we should find all the relationships describing person and horse (N) and the exact relationships of person-ride-horse (M). We use N and M to denote the number of the above two relationships, and p(ride|person, horse) can be simply acquired as N/M. It has the following format: `(subject, object, predicate)`. Original shape=(100,100,70), where 100 are the number of classes and 70 the number of relationships.

p(ride|person, horse) = \frac{#(person, horse, *)}{#(person, horse, ride)}
