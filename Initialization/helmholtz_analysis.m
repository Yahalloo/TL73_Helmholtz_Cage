%% Read exported data
t = out.B_actual.Time(:);
B = out.B_actual.Data(:);       % Assumed already in uT
I = out.I_coil.Data(:);         % A
V = out.V_coil.Data(:);         % V
T = out.T_coil.Data(:);         % K

%% Test settings
ss = t >= 1.0 & t <= 1.9;       % Steady-state window [s]
B_initial = 100;               % Target before step [uT]
B_final = -100;                % Target after step [uT]
step_time = 0.3;               % s

%% Maximum temperature, current and voltage
fprintf('Maximum temperature: %.2f °C\n', max(T)-273.15);
fprintf('Peak current: %.3f A\n', max(abs(I)));
fprintf('Peak voltage: %.3f V\n', max(abs(V)));

%% Field ripple and steady-state error
B_ss = B(ss);
t_ss = t(ss);

B_mean = trapz(t_ss,B_ss)/(t_ss(end)-t_ss(1));

fprintf('Peak-to-peak field ripple: %.4f uT\n', max(B_ss)-min(B_ss));
fprintf('Absolute steady-state error: %.4f uT\n', abs(B_final-B_mean));

%% 10–90%% slew rate
idx = t >= step_time & t < 1.0;
tt = t(idx);
progress = (B(idx)-B_initial)/(B_final-B_initial);

i10 = find(progress >= 0.1,1);
i90 = find(progress >= 0.9,1);

if ~isempty(i10) && ~isempty(i90) && tt(i90) > tt(i10)
    slew = 0.8*abs(B_final-B_initial)/(tt(i90)-tt(i10));
    fprintf('10–90%% slew rate: %.2f uT/s\n', slew);
else
    fprintf('Slew rate: transition not captured.\n');
end