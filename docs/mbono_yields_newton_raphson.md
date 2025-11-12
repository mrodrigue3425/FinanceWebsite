# Newton-Raphson for Banxico Mbono Price-to-Yield Conversion

### Algorithm

The Newton-Raphson algorithm iteratively finds the roots of a function $f(r)$ by starting with a guess $r_0$.

The gradient of $f$ at $r_0$ is given by:

$$
f'(r_0) = \frac{f(r_0)}{r_0 - r_1}
$$

where $r_1$ is intended to move closer to the root than $r_0$, and is found by rearranging the above to give:

$$
r_1 = r_0 - \frac{f(r_0)}{f'(r_0)}
$$

In general, we have:

$$
r_{n+1} = r_n - \frac{f(r_n)}{f'(r_n)}
$$

As we get closer to the root, $f(r_n)$ becomes smaller, making the differences in $r$ between iterations progressively smaller.

---

### Mbono Pricing

The clean price of an Mbono is computed by bringing outstanding payments (coupon and principal) to present value and subtracting the accrued interest as

$$
P = \sum_{j=1}^{K} \frac{C_j}{(1+R)^{j-\frac{d}{N_1}}} + \frac{VN}{(1+R)^{K-\frac{d}{N_1}}} - C_1 * \frac{d}{N_1}
$$

**(1)**

where $K$ is the number of outstanding coupon payments as of settle date, and $C_j$ is the $j^{th}$ coupon cashflow after settle date, which is calculated as

$$
C_j = VN * \frac{TC * N_j}{360}
$$

where $VN$ is the par value (MXN 100 for all Mbonos), $TC$ is the fixed coupon rate, and $N_j$ is the adjusted number of calendar days in the $j^{th}$ coupon period.

$R$ is the discount rate, using the annualised yield to maturity as

$$
R = r * \frac{N_j}{360}
$$

The accrued interest is calculated using $N_1$, the current coupon period's length in days, and $d$, the days accrued since the start of the current coupon period as of settle.

---

To simplify pricing, we can rewrite equation (1) in coupon cashflow, principal cashflow, and accrued interest components ($PV_C$, $PV_P$, and $I_{acc}$) as

$$
P = PV_C + PV_P + I_{acc}
$$

**(2)**

and assume that all coupon periods are 182 calendar days long, with cashflows unadjusted for bumping, i.e,

$$
N_j = N = 182 \quad ; \quad C_j = C = VN * \frac{182 * TC}{360} \quad \forall j
$$

and

$$
PV_C = C * \left(\frac{1}{(1+R)^{1-\frac{d}{N}}} + \frac{1}{(1+R)^{2-\frac{d}{N}}} + ... + \frac{1}{(1+R)^{K-\frac{d}{N}}}\right) = C * S
$$

If we let $a = 1 + R$, we get:

$$
S = \frac{1}{a^{1-\frac{d}{N}}} + \frac{1}{a^{2-\frac{d}{N}}} + ... + \frac{1}{a^{K-\frac{d}{N}}}
$$

$$
Sa = \frac{1}{a^{-\frac{d}{N}}} + \frac{1}{a^{1-\frac{d}{N}}} + ... + \frac{1}{a^{K-1-\frac{d}{N}}}
$$

$$
Sa - S = a^{\frac{d}{N}}\left(1 - \frac{1}{a^K}\right)
$$

$$
S(a - 1) = a^{\frac{d}{N}}\left(1 - a^{-K}\right)
$$

Substituting $1 + R$ back in:

$$
S = (1+R)^{\frac{d}{N}}\left(\frac{1 - (1+R)^{-K}}{R}\right)
$$

and so

$$
PV_C = C(1+R)^{\frac{d}{N}}\left(\frac{1 - (1+R)^{-K}}{R}\right)
$$

**(3)**

Substituting equation (3) back into (2), we get

$$
P = C(1+R)^{\frac{d}{N}}\left(\frac{1 - (1+R)^{-K}}{R}\right) + \frac{VN}{(1+R)^{K-\frac{d}{N}}} - C * \frac{d}{N}
$$

Factoring out $(1+R)^{\frac{d}{N}-1}$ from the first two components we get

$$
P = \frac{1}{(1+R)^{1-\frac{d}{N}}}\left[C(1+R)\left(\frac{1}{R} - \frac{1}{R(1+R)^K}\right) + \frac{VN}{(1+R)^{K-1}}\right] - C * \frac{d}{N}
$$

$$
P = \frac{1}{(1+R)^{1-\frac{d}{N}}}\left[C\left(1 + \frac{1}{R} - \frac{1}{R(1+R)^{K-1}}\right) + \frac{VN}{(1+R)^{K-1}}\right] - C * \frac{d}{N}
$$

$$
\boxed{
P = \frac{C + C\left[\frac{1}{R} - \frac{1}{R(1+R)^{K-1}}\right] + \frac{VN}{(1+R)^{K-1}}}{(1+R)^{1-\frac{d}{N}}} - C * \frac{d}{N}
}
$$

**(4)**

$$
\boxed{
\begin{gathered}
R = r * \frac{N}{360} \quad ; \quad r \text{ is the annualised yield to maturity} \\
C = VN * \frac{N * TC}{360} \\
N = 182
\end{gathered}
}
$$

Source: [Banxico Mbono Price-to-Yield Reference (PDF, p. 7)][banxico-ref]

[banxico-ref]: https://www.banxico.org.mx/markets/d/%7B8754BE29-978F-0496-8905-E992820163BC%7D.pdf

---

### Implementing Newton-Raphson to Solve Equation (4) for $r$

We let

$$
f(R) = \frac{C + C\left[\frac{1}{R} - \frac{1}{R(1+R)^{K-1}}\right] + \frac{VN}{(1+R)^{K-1}}}{(1+R)^{1-\frac{d}{N}}} - C * \frac{d}{N} - P
$$

Expanding

$$
f(R) = \frac{C}{(1+R)^{1-\frac{d}{N}}} + \frac{C}{R(1+R)^{1-\frac{d}{N}}} - \frac{C}{R(1+R)^{K-\frac{d}{N}}} + \frac{VN}{(1+R)^{K-\frac{d}{N}}} - C * \frac{d}{N} - P
$$

$$
f(R) = \alpha + \beta - \gamma + \sigma - C * \frac{d}{N} - P
$$

Now, for the algorithm we require $f'(r)$ to be

$$
f'(r) = \frac{df}{dR}\frac{dR}{dr}
$$

where $\frac{dR}{dr} = \frac{182}{360}$, which means

$$
f'(r) = \frac{182}{360}\left(\frac{d\alpha}{dR} + \frac{d\beta}{dR} - \frac{d\gamma}{dR} + \frac{d\sigma}{dR}\right)
$$

where

$$
\begin{aligned}
\frac{d\alpha}{dR} &= C\left(\frac{d}{N}-1\right)(1+R)^{\frac{d}{N}-2} \\
\frac{d\beta}{dR} &= C\left[\frac{1}{R}\left(\frac{d}{N}-1\right)(1+R)^{\frac{d}{N}-2} - \frac{1}{R^2}(1+R)^{\frac{d}{N}-1}\right] \\
\frac{d\gamma}{dR} &= C\left[\frac{1}{R}\left(\frac{d}{N}-K\right)(1+R)^{\frac{d}{N}-K-1} - \frac{1}{R^2}(1+R)^{\frac{d}{N}-K}\right] \\
\frac{d\sigma}{dR} &= VN\left(\frac{d}{N}-K\right)(1+R)^{\frac{d}{N}-K-1}
\end{aligned}
$$

Therefore

$$
\begin{aligned}
f'(r) = \frac{182}{360}\Big[ 
&C\left(\frac{d}{N}-1\right)(1+R)^{\frac{d}{N}-2} + \\
&C\left[\frac{1}{R}\left(\frac{d}{N}-1\right)(1+R)^{\frac{d}{N}-2} - \frac{1}{R^2}(1+R)^{\frac{d}{N}-1}\right] - \\
&C\left[\frac{1}{R}\left(\frac{d}{N}-K\right)(1+R)^{\frac{d}{N}-K-1} - \frac{1}{R^2}(1+R)^{\frac{d}{N}-K}\right] + \\
&VN\left(\frac{d}{N}-K\right)(1+R)^{\frac{d}{N}-K-1}
\Big]
\end{aligned}
$$

where

$$
R = r * \frac{182}{360}
$$
