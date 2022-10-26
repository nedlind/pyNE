# Select source object (Rebar)

# Get original length

# Get bar diameter

# Read splice length Ls from source object

# Get vectors for bar direction and distribution direction

# Set max bar length Lmax = 12000 mm

# Set min bar length Lmin = 4000 mm

# Calvulate number of splices
# n = Math.Floor((L - 2.3*Ls) / (Lmax - 2.3*2.3*Ls));

# Calculate start and end bar lenght
# La = L-n*(Lmax-Ls);
# Lb = L-Lmin-(n-1)*Lmax+n*Ls;
# if La < Lmin:
#   Lstart = Lmin
#   Lend = Lb
# else:
#   Lstart = La
#   Lend = Lmax;