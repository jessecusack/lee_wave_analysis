function [] = W_model(EMF, param_file)
% Input: 
%   EMApexFLoat class
%   Path to paramter file
% Output:
%   Saves model output to .mat file.

run(param_file)

% Am only doing it for profiles 1:300 for the moment because I do not have
% the correct data quality controls in place. (Some profiles at hpid > 300
% do not have enough data to produce the grid and need to be discarded.)
[~, Pg, Wf] = EMF.gridVar(hpidIndx, 'P', PLvls, 'Wef');
[~, ~, pc] = EMF.gridVar(hpidIndx, 'P', PLvls, 'pc_ctd');
[~, ~, dens] = EMF.gridVar(hpidIndx, 'P', PLvls, 'pdens');
dens = dens.^(-1);
% Subtract mean density profile.
% dens = dens - repmat(mean(dens, 2), 1, size(dens, 2));

[~, validHpidIndx] = EMF.getPflSubset(hpidIndx);

oddPfls = rem(validHpidIndx, 2) == 1;
evenPfls = rem(validHpidIndx, 2) == 0;
allPfls =  oddPfls | evenPfls;

% Calculate w^2 - will use thsi for drag calculation
% Change sign of w**2 to be negative on the up profiles
% (Although this is the opposite convention from what I am using for the
% float absolute velocity?)
Wf2 = Wf.^2;
Wf2(:,evenPfls) = -Wf2(:,evenPfls);

% What profiles to choose? What depth levels to use?
if useOdd
    usePfls = oddPfls;
elseif useEven
    usePfls = evenPfls;
else
    usePfls = allPfls;
end

useLvls = 1:size(pc,1);

Wf2_ = Wf2(useLvls,usePfls);
pc_ = pc(useLvls,usePfls);
Pg_ = Pg(useLvls,usePfls);
dens_ = dens(useLvls,usePfls);

fprintf(1,'Wref\t\tkappa\t\talpha\t\tk0\t\tmeanErr\n');

x = zeros(NGrps,4); Wref = zeros(NGrps,1); alpha = zeros(NGrps,1); 
kappa = zeros(NGrps,1); k0 = zeros(NGrps,1); meanErr = zeros(NGrps,1);
sx = zeros(NGrps,4);
for i = 1:NGrps
    
    % Don't want to include imaginary results for Wref!
    while x(i,4) <= 0
        
        [~, idx] = datasample(Wf2_, NPfls, 2);
        % Solve equation Ax = B for x using lscov.
        B = reshape(Wf2_(:,idx),[],1);
        A(:,2) = reshape(pc_(:,idx),[],1);
        A(:,3) = reshape(Pg_(:,idx),[],1);
        A(:,4) = reshape(dens_(:,idx),[],1);
        A(:,1) = 1;

        % Exclude very large velocities 
        ix = abs(B) < 0.03;

        % Now find parameters by least squares minimisation of residual 
        [x(i,:), sx(i,:)] = lscov(A(ix,:),B(ix));
    end

    Wref(i) = sqrt(x(i,4)/dens0);
    alpha(i) = -x(i,2)*dens0/x(i,4);
    kappa(i) = x(i,3)*dens0/x(i,4);
    k0(i) = -x(i,1)/x(i,2) - x(i,4)/(x(i,2)*dens0);

    % Given these parameters this is hte modeled value of squared velocity
    Wrel2 = Wrel2_model_lin(x(i,:), pc, Pg, dens);

    % Difference between actual data and modelled data (both are w^2)
    % Form thsi we coudl sovle for water vertical velocity
    err2 = Wf2 - Wrel2;
    meanErr(i) = mean(reshape(err2,[],1));
    fprintf(1,'%3.3f\t\t%6.2e\t%6.2e\t%5.1f\t\t%6.2e\n',...
        Wref(i), kappa(i), alpha(i), k0(i), meanErr(i));
end

mabcd = mean(x);

fprintf(1, 'Mean values:\n');
fprintf(1,'%3.3f\t\t%6.2e\t%6.2e\t%5.1f\t\t%6.2e\n',...
        mean(Wref), mean(kappa), mean(alpha), mean(k0), mean(meanErr));
fprintf(1, 'Standard deviation:\n');
fprintf(1,'%3.3f\t\t%6.2e\t%6.2e\t%5.1f\t\t%6.2e\n',...
        std(Wref), std(kappa), std(alpha), std(k0), std(meanErr));

% Wrel = Wrel_model_lin(mabcd, pc, Pg, dens, validHpidIndx);
% Wwat = Wf - Wrel;

save(saveFName, 'x', 'sx', 'mabcd', 'dens0')

