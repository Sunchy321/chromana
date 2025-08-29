export interface Icon {
    name:     string;
    class:    string;
    ligature: string;
    game?:    string; // 游戏名称
}

export interface IconsData {
    icons: Icon[];
}

export interface GameConfig {
    name:            string;
    ligature_prefix: string;
}
