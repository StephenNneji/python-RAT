import ratapi


p1, r = ratapi.examples.normal_reflectivity.DSPC_standard_layers.DSPC_standard_layers()

c = ratapi.Controls()
c.procedure = 'dream'
c.display = 'final'

p2, r = ratapi.run(p1, c)
