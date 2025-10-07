import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class KolamDraw(object):
    """
    Core class for kolam generation using a gating structure.

    The algorithm uses a matrix-based approach where gates control the path
    direction around each dot in the grid. Four-fold symmetry is maintained
    to ensure balanced and aesthetically pleasing patterns.
    """

    def __init__(self, ND):
        """Initialize kolam drawer with grid dimension."""
        self.ND = ND
        self.Nx = ND + 1
        self.A1 = np.ones((self.Nx, self.Nx)) * 99
        self.F1 = np.ones((self.Nx, self.Nx))
        self.Ns = (2 * (ND ** 2) + 1) * 5
        self.boundary_type = 'diamond'

    def set_boundary(self, boundary_type='diamond'):
        """
        Configure the boundary shape for pattern generation.

        Available boundary types include diamond (full grid), corners,
        fish (concentric rings), waves, fractal, and organic.
        """
        self.boundary_type = boundary_type

    def is_inside_boundary(self, i, j):
        """
        Determine if a given grid point lies within the active boundary.

        This method implements different geometric constraints based on
        the selected boundary type, allowing for diverse pattern shapes.
        """
        ND = self.ND
        x = i - ND
        y = j - ND

        if self.boundary_type == 'diamond':
            return True

        elif self.boundary_type == 'corners':
            threshold = ND * 0.3
            return (abs(x) >= threshold) and (abs(y) >= threshold)

        elif self.boundary_type == 'fish':
            # Fish pattern: concentric rings (bullseye)
            dist = np.sqrt(x**2 + y**2)
            ring_width = ND * 0.35
            ring_num = int(dist / ring_width)
            return (ring_num % 2) == 0

        elif self.boundary_type == 'waves':
            freq = 2 * np.pi / (ND * 0.6)
            wave1 = np.sin(x * freq)
            wave2 = np.sin(y * freq)
            interference = wave1 + wave2
            return interference > 0

        elif self.boundary_type == 'fractal':
            xi = int(abs(x) + ND)
            yi = int(abs(y) + ND)
            return (xi & yi) % 4 < 2

        elif self.boundary_type == 'organic':
            dist = np.sqrt(x**2 + y**2)
            angle = np.arctan2(y, x)
            wobble = np.sin(angle * 3) * ND * 0.2
            max_dist = ND * 0.8 + wobble
            return dist < max_dist

        return True

    def ResetGateMatrix(self):
        """
        Initialize gate and flag matrices with boundary conditions.

        Sets up the gate matrix (A) and flag matrix (F) with appropriate
        boundary values and diagonal constraints. Applies the selected
        boundary mask to restrict pattern generation to valid regions.
        """
        Nx2 = int(self.Nx / 2)
        Nx1 = self.Nx - 1
        A = self.A1 * 1
        F = self.F1 * 1

        # Set boundary conditions
        for i in range(self.Nx):
            A[0, i] = A[i, 0] = A[self.Nx - 1, i] = A[i, self.Nx - 1] = 0
            F[0, i] = F[i, 0] = F[self.Nx - 1, i] = F[i, self.Nx - 1] = 0

        # Set diagonal constraints
        for i in range(1, self.Nx - 1):
            A[i, i] = A[i, self.Nx - 1 - i] = 1
            F[i, i] = F[i, self.Nx - 1 - i] = 0

        # Apply custom boundary constraints
        if self.boundary_type != 'diamond':
            for i in range(self.Nx):
                for j in range(self.Nx):
                    if not self.is_inside_boundary(i, j):
                        A[i, j] = 0
                        F[i, j] = 0

        return A, F

    def toss(self, bias):
        """Generate a random binary value with specified bias."""
        x = np.random.randint(0, 1000) / 1000
        return 1 if x > bias else 0

    def AssignGates(self, krRef, Kp, Ki):
        """
        Assign gate values using PI controller for aesthetic control.

        This method implements a proportional-integral controller to maintain
        the desired ratio of open gates (determined by sigmaref). Four-fold
        symmetry is enforced by simultaneous assignment to symmetric positions.
        """
        A, F = self.ResetGateMatrix()
        errAckr = 0.0
        count1 = 0
        count01 = 1
        Nx1 = self.Nx - 1
        Nx2 = int(self.Nx / 2)

        for i in range(1, Nx2):
            for j in range(i, self.Nx - i):
                # PI controller for gate ratio
                errkr = krRef - (count1 / count01)
                errAckr = errAckr + errkr
                kr = krRef + Kp * errkr + Ki * errAckr

                if F[i, j] == 1:
                    if F[i, j + 1] == 1:
                        # Symmetric gate assignment (four-fold)
                        A[i, j] = A[j, i] = A[Nx1 - i, Nx1 - j] = A[Nx1 - j, Nx1 - i] = self.toss(kr)
                        F[i, j] = F[j, i] = F[Nx1 - i, Nx1 - j] = F[Nx1 - j, Nx1 - i] = 0
                        count01 = count01 + 4
                        if A[i, j] > 0.9:
                            count1 = count1 + 4
                        if A[i - 1, j] + A[i - 1, j + 1] + A[i, j] < 0.1:
                            x = 1
                        else:
                            x = self.toss(kr)
                        A[i, j + 1] = A[j + 1, i] = A[Nx1 - i, Nx1 - 1 - j] = A[Nx1 - 1 - j, Nx1 - i] = x
                        F[i, j + 1] = F[j + 1, i] = F[Nx1 - i, Nx1 - 1 - j] = F[Nx1 - 1 - j, Nx1 - i] = 0
                        count01 = count01 + 4
                        if A[i, j + 1] > 0.9:
                            count1 = count1 + 4
                    if F[i, j + 1] == 0:
                        if A[i - 1, j] + A[i - 1, j + 1] + A[i, j + 1] < 0.1:
                            x = 1
                        else:
                            x = self.toss(kr)
                        A[i, j] = A[j, i] = A[Nx1 - i, Nx1 - j] = A[Nx1 - j, Nx1 - i] = x
                        F[i, j] = F[j, i] = F[Nx1 - i, Nx1 - j] = F[Nx1 - j, Nx1 - i] = 0
                        count01 = count01 + 4
                        if A[i, j] > 0.9:
                            count1 = count1 + 4
                if F[i, j] == 0:
                    if F[i, j + 1] == 1:
                        if A[i - 1, j] + A[i - 1, j + 1] + A[i, j] < 0.1:
                            x = 1
                        else:
                            x = self.toss(kr)
                        A[i, j + 1] = A[j + 1, i] = A[Nx1 - i, Nx1 - 1 - j] = A[Nx1 - 1 - j, Nx1 - i] = x
                        F[i, j + 1] = F[j + 1, i] = F[Nx1 - i, Nx1 - 1 - j] = F[Nx1 - 1 - j, Nx1 - i] = 0
                        count01 = count01 + 4
                        if A[i, j + 1] > 0.9:
                            count1 = count1 + 4
        return A, F, kr

    def NextStep(self, icg, jcg, ce):
        """
        Calculate next position in the kolam path based on current gate.

        Implements the path evolution rules that determine how the drawing
        moves from one position to the next, considering the gate values
        and current direction.
        """
        icgx = icg + self.ND
        jcx = jcg + self.ND
        icgx2 = int(np.floor(icgx / 2))
        jcx2 = int(np.floor(jcx / 2))

        calpha = np.mod(ce, 2)
        cbeta = -1 if ce > 1 else 1
        cgamma = -1 if np.mod(int(icgx + jcx), 4) == 0 else 1
        cg = 1 if self.A[icgx2, jcx2] > 0.5 else 0

        cgd = 1 - cg
        calphad = 1 - calpha
        nalpha = cg * calpha + cgd * calphad
        nbeta = (cg + cgd * cgamma) * cbeta
        nh = (calphad * cgamma * cgd + calpha * cg) * cbeta
        nv = (calpha * cgamma * cgd + calphad * cg) * cbeta

        ing = int(icg + nh * 2)
        jng = int(jcg + nv * 2)
        ingp = icg + cgd * (calphad * cgamma - calpha) * cbeta * 0.5
        jngp = jcg + cgd * (calpha * cgamma - calphad) * cbeta * 0.5

        ne = 0 if nalpha == 0 and nbeta == 1 else (2 if nalpha == 0 else (1 if nbeta == 1 else 3))
        return ing, jng, ne, ingp, jngp

    def XNextSteps(self, icgo, jcgo, ceo, Ns):
        """Generate complete path sequence from starting position."""
        ijcx = np.zeros((Ns, 2))
        cex = np.zeros(Ns)
        ijcp = np.zeros((Ns, 2))
        ijcx[0, :] = [icgo, jcgo]
        cex[0] = ceo

        for i in range(Ns - 1):
            ijcx[i + 1, 0], ijcx[i + 1, 1], cex[i + 1], ijcp[i, 0], ijcp[i, 1] = self.NextStep(
                ijcx[i, 0], ijcx[i, 1], cex[i]
            )
        return ijcx, cex, ijcp

    def PathCount(self):
        """
        Count path length until it returns to starting position.

        Traces the kolam path from a random starting point and counts
        the number of steps until the path closes (returns to start with
        same direction). This is used to verify one-stroke completion.
        """
        Ns, isx, isa = self.Ns, 0, 0
        ijcx = np.zeros((Ns, 2))
        cex = np.zeros(Ns)
        ijcp = np.zeros((Ns, 2))
        ijcx[0, 0] = 2 * np.random.randint(0, 2) - 1
        ijcx[0, 1] = 2 * np.random.randint(0, 2) - 1
        cex[0] = 0

        while isa < Ns - 2:
            isa += 1
            ijcx[isa, 0], ijcx[isa, 1], cex[isa], ijcp[isa - 1, 0], ijcp[isa - 1, 1] = self.NextStep(
                ijcx[isa - 1, 0], ijcx[isa - 1, 1], cex[isa - 1]
            )
            if int(ijcx[isa, 0]) == int(ijcx[0, 0]) and int(ijcx[isa, 1]) == int(ijcx[0, 1]) and int(cex[isa]) == int(cex[0]):
                isx = isa
                break
        return isx

    def Dice(self, krRef, Kp, Ki, Nthr):
        """
        Generate multiple gate configurations and select the best one.

        Creates several random gate assignments and evaluates them based
        on path length, keeping the configuration that produces the longest
        one-stroke path.
        """
        Ns, ith, ithx, ismax = self.Ns, 0, 0, 0
        ijcx, cex, ijcp = np.zeros((Ns, 2)), np.zeros(Ns), np.zeros((Ns, 2))
        krx = np.zeros(Nthr)
        Amax = self.A1 * 1

        while ith < Nthr:
            self.A, self.F, krx[ith] = self.AssignGates(krRef, Kp, Ki)
            Flag1 = Flag2 = isx = isa = 0
            ijcx[0, 0] = ijcx[0, 1] = 1
            cex[0] = 0

            while isa < Ns - 2:
                isa += 1
                ijcx[isa, 0], ijcx[isa, 1], cex[isa], ijcp[isa - 1, 0], ijcp[isa - 1, 1] = self.NextStep(
                    ijcx[isa - 1, 0], ijcx[isa - 1, 1], cex[isa - 1]
                )
                if int(ijcx[isa, 0]) == int(ijcx[0, 0]) and int(ijcx[isa, 1]) == int(ijcx[0, 1]) and int(cex[isa]) == int(cex[0]):
                    Flag1, isx = 1, isa
                    break

            if Flag1 == 1:
                if isx < Ns + 2:
                    Flag2 = 1
                    if isx > ismax:
                        ismax, Amax = isx, self.A * 1
                if isx > (Ns / 2) - 2:
                    Flag2, ithx, ith = 2, ith, Nthr + 1

            ith += 1

        return self.A, self.F, Amax, isx, ithx, ismax, Flag1, Flag2, krx

    def SwitchGate(self, ig, jg):
        """Toggle a gate value while maintaining symmetry."""
        Flag, Ax, Fx, Nx = 0, self.A * 1, self.F * 1, self.Nx

        if Ax[ig, jg] < 0.1:
            Ax[ig, jg] = Ax[jg, ig] = Ax[Nx - ig - 1, Nx - jg - 1] = Ax[Nx - jg - 1, Nx - ig - 1] = 1
            Fx[ig, jg] = Fx[jg, ig] = Fx[Nx - ig - 1, Nx - jg - 1] = Fx[Nx - jg - 1, Nx - ig - 1] = 0
            Flag = 1
        elif Ax[ig, jg] > 0.9:
            Ax[ig, jg] = Ax[jg, ig] = Ax[Nx - ig - 1, Nx - jg - 1] = Ax[Nx - jg - 1, Nx - ig - 1] = 0
            Fx[ig, jg] = Fx[jg, ig] = Fx[Nx - ig - 1, Nx - jg - 1] = Fx[Nx - jg - 1, Nx - ig - 1] = 0
            Flag = -1
        return Ax, Fx, Flag

    def FlipTestSwitch(self, ksh, iL, iH):
        """
        Test gate flips to improve path length.

        Randomly selects gates to flip and evaluates if the change
        improves the path length. Keeps beneficial changes and reverts
        detrimental ones.
        """
        Ncx, Ns, Nx2 = self.PathCount(), self.Ns, int(self.Nx / 2)
        iLx, iHx = max(min(iL, Nx2), 1), max(min(iH, Nx2), max(min(iL, Nx2), 1))

        for ig in range(iLx, iHx):
            for jg in range(ig, self.Nx - 1 - ig):
                Ax, Fx = self.A * 1, self.F * 1
                if self.F[ig, jg] == 0 and self.toss(ksh) == 1:
                    self.A, self.F, Flag = self.SwitchGate(ig, jg)
                    Nc = self.PathCount()
                    if Nc < Ncx:
                        self.A, self.F = Ax, Fx
                    elif Nc >= Ncx:
                        Ncx = Nc
                    if Ncx >= Ns - 5:
                        break
        return Ncx

    def IterFlipTestSwitch(self, ksh, Niter, iL, iH):
        """
        Iteratively improve gate configuration through random flips.

        Performs multiple iterations of gate flipping to optimize the
        path length, converging towards a complete one-stroke kolam.
        """
        Ns, Ncx = self.Ns, self.PathCount()
        if Ncx < Ns:
            for iter in range(Niter):
                Ncx = self.FlipTestSwitch(ksh, iL, iH)
                if Ncx >= Ns - 5:
                    break
        return Ncx, self.A, self.F



def plotkolam(ijngp, kolam_color='#1f77b4', theme='light'):
    """
    Render the kolam pattern with specified visual theme.

    Creates a matplotlib figure displaying the kolam path with
    customizable colors and background theme (light or dark).
    """
    if theme.lower() == 'dark':
        bg_color = '#1a1a1a'
    else:
        bg_color = 'white'

    fig, ax = plt.subplots(figsize=(12, 12), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    ijngpx = (ijngp[:, 0] + ijngp[:, 1]) / 2
    ijngpy = (ijngp[:, 0] - ijngp[:, 1]) / 2

    ax.plot(ijngpx[:-1], ijngpy[:-1], color=kolam_color, linewidth=2.5, alpha=0.95)

    ND = int(np.max(np.abs(ijngp))) + 2
    plt.axis('equal')
    plt.axis('off')
    plt.xlim(-ND-1, ND+1)
    plt.ylim(-ND-1, ND+1)

    plt.tight_layout()
    plt.show()
    return fig


def GenerateKolam(ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None):
    """
    Main function to generate and display a kolam pattern.

    Parameters
    ----------
    ND : int
        Grid dimension (number of dots per side, must be odd)
    sigmaref : float
        Aesthetic parameter controlling gate density (0 to 1)
        Higher values produce more complex patterns
    boundary_type : str
        Shape constraint: 'diamond', 'corners', 'fish', 'waves',
        'fractal', or 'organic'
    theme : str
        Visual theme: 'light' or 'dark'
    kolam_color : str
        Path color (color name or hex code)

    Returns
    -------
    tuple
        Gate matrix and path length
    """
    default_colors = {
        'diamond': '#e377c2',
        'corners': '#1f77b4',
        'fish': '#ff7f0e',
        'waves': '#2ca02c',
        'fractal': '#9467bd',
        'organic': '#8c564b'
    }

    if kolam_color is None:
        kolam_color = default_colors.get(boundary_type, '#1f77b4')

    Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 40, 10
    krRef = 1 - sigmaref

    KD = KolamDraw(ND)
    KD.set_boundary(boundary_type)

    A2, F2, A2max, isx, ithx, ismax, Flag1, Flag2, krx2 = KD.Dice(krRef, Kp, Ki, Nthr)

    Ncx = KD.PathCount()
    Nx2x = int((ND + 1) / 2)
    Ncx, GM, GF = KD.IterFlipTestSwitch(ksh, Niter, 1, Nx2x)

    Ns = (2 * (ND ** 2) + 1) * 5
    ijng, ne, ijngp = KD.XNextSteps(1, 1, 1, Ns)

    plotkolam(ijngp, kolam_color, theme)
    return GM, Ncx


if __name__ == "__main__":
    np.random.seed(42)

    GenerateKolam(19, 0.65, 'fractal', theme='light', kolam_color='brown')
    GenerateKolam(19, 0.65, 'waves', theme='dark', kolam_color='white')
    GenerateKolam(19, 0.65, 'fish', theme='dark', kolam_color='cyan')

