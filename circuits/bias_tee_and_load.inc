* Full external circuit; all capacitances remain explicit.
* R3 is the detector source-return series resistor, not an RF shunt.
R1 N001 N008 10k
L1 N008 N012 19894n Cpar=1p
C1 N013 N012 7.957n Rser=1
R20 N013 0 {Rextra}
R2 N013 0 50
C12 N013 0 {Cshunt}
R3 N024 0 20
