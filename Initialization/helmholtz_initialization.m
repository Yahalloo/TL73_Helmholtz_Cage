% 1. INITIALIZE
% All physical parameters below are provisional until measured/validated.
R = 6;                       % Coil resistance at reference temperature [ohm]
L = 10e-3;                   % Coil inductance [H]: 0.01 H, NOT 0.1 H
k = 50e-6;                   % Coil field/current gain [T/A]
Vmax = 24;                   % DC bus [V]
Bambient = 20e-6;            % Constant ambient field along this axis [T]
T_threshold = 313.15;        % Thermal trip threshold [K]

% PWM: both generators use identical timing and zero phase delay.
PWM_mode = 0;   % Unipolar
%PWM_mode = 1; % Bipolar

fpwm = 10e3;                 % Each leg's switching frequency [Hz]
Tpwm = 1/fpwm;               % Full PWM period [s]
T_pwm_timer = Tpwm/2;        % Simscape PWM Generator: Up-Down timer period [s]
Kpwm = 1/Vmax;               % Signed voltage command -> m in [-1,1]
t_dead = 5e-9;               % Turn-on delay [s]; validate against driver/timing


% Thermal Resistor block and external thermal network
R_coil_ref = R;              % Avoid two independent nominal resistance values
T_coil_ref = 293.15;         % Reference temperature [K]
alpha_coil = 0.00393;        % Resistance temperature coefficient [1/K]
tau_coil_th = 200;           % Thermal Resistor time constant [s]
G_coil_loss = 0.5;           % Thermal Resistor dissipation factor [W/K]
R_th = 2;                   % External Thermal Resistance block [K/W]